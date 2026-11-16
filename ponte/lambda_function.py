"""Ponte in Europa per i file del MIMIT: funzione AWS Lambda nella regione di Francoforte.

Perché esiste: il sito del MIMIT risponde solo alle connessioni dall'Europa, e i server di
GitHub Actions sono negli USA. Ogni mattina l'Action chiede qui i due file; questa funzione
li scarica dall'Europa e li restituisce compressi con gzip (da 7,5 MB a meno di 2 MB).

Cosa fa e cosa no:
- risponde solo a chi manda l'intestazione X-Chiave-Ponte uguale alla variabile
  d'ambiente CHIAVE_PONTE (se la variabile manca, rifiuta tutto);
- scarica solo i due file del MIMIT, scelti con ?file=anagrafica o ?file=prezzi:
  non accetta indirizzi da fuori, quindi non è un proxy aperto.

Un file solo e solo la libreria standard di Python: su AWS si carica così com'è.
Installazione: ponte/README.md.
"""

import base64
import gzip
import hmac
import os
import urllib.request

# Devono restare uguali a quelli di pipeline/scarica.py (lo controlla tests/test_ponte.py)
FILE = {
    "anagrafica": "https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv",
    "prezzi": "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv",
}

USER_AGENT = "prezzi-carburanti-terni/0.1 (ponte AWS per gli open data MIMIT)"
TIMEOUT_SECONDI = 50  # la funzione su AWS ha 60 secondi in tutto


def _testo(stato: int, messaggio: str) -> dict:
    return {"statusCode": stato, "headers": {"Content-Type": "text/plain; charset=utf-8"}, "body": messaggio}


def lambda_handler(evento, contesto, apri=urllib.request.urlopen, ambiente=os.environ):
    """Punto d'ingresso chiamato da AWS. `apri` e `ambiente` si sostituiscono nei test."""
    chiave_attesa = ambiente.get("CHIAVE_PONTE", "")
    intestazioni = {nome.lower(): valore for nome, valore in (evento.get("headers") or {}).items()}
    chiave = intestazioni.get("x-chiave-ponte", "")
    if not chiave_attesa or not hmac.compare_digest(chiave.encode(), chiave_attesa.encode()):
        return _testo(403, "chiave mancante o sbagliata")

    nome = (evento.get("queryStringParameters") or {}).get("file")
    if nome not in FILE:
        return _testo(404, "file sconosciuto: usa ?file=anagrafica oppure ?file=prezzi")

    richiesta = urllib.request.Request(FILE[nome], headers={"User-Agent": USER_AGENT})
    try:
        with apri(richiesta, timeout=TIMEOUT_SECONDI) as risposta:
            if risposta.status != 200:
                return _testo(502, f"il MIMIT ha risposto HTTP {risposta.status}")
            corpo = risposta.read()
    except OSError as errore:  # rete, timeout, HTTPError
        return _testo(504, f"il MIMIT non risponde: {errore}")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/gzip"},
        "isBase64Encoded": True,
        "body": base64.b64encode(gzip.compress(corpo)).decode("ascii"),
    }
