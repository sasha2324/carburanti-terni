"""Download dei file MIMIT, con tentativi ripetuti e messaggi d'errore chiari.

Il sito del MIMIT risponde solo alle connessioni dall'Europa: dai server di GitHub (USA)
la connessione non si apre. Per questo, se sono impostate le variabili d'ambiente
MIMIT_PONTE_URL e MIMIT_PONTE_CHIAVE, i file si chiedono al «ponte»: una piccola funzione
su AWS a Francoforte (cartella ponte/) che li scarica dall'Europa e li restituisce compressi.
Senza quelle variabili (per esempio sul Mac) si scarica direttamente dal MIMIT.
"""

import gzip
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from pipeline.leggi import FormatoNonValido

URL_ANAGRAFICA = "https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv"
URL_PREZZI = "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"

# Nome con cui il ponte conosce ciascun file
FILE_DEL_PONTE = {URL_ANAGRAFICA: "anagrafica", URL_PREZZI: "prezzi"}

USER_AGENT = "prezzi-carburanti-terni/0.1 (sito statico con open data MIMIT)"
TIMEOUT_SECONDI = 60
TENTATIVI = 3
PAUSA_SECONDI = 30


class ErroreDownload(Exception):
    """Il file non è arrivato: rete, server o risposta inattesa."""


def _richiesta(url: str, ambiente) -> tuple[urllib.request.Request, str]:
    """La richiesta da fare e una descrizione per i messaggi d'errore."""
    ponte = ambiente.get("MIMIT_PONTE_URL", "").strip()
    chiave = ambiente.get("MIMIT_PONTE_CHIAVE", "").strip()
    if not (ponte and chiave):
        return urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), url
    if url not in FILE_DEL_PONTE:
        raise ErroreDownload(f"il ponte conosce solo i due file del MIMIT, non {url}")
    indirizzo = f"{ponte}?{urllib.parse.urlencode({'file': FILE_DEL_PONTE[url]})}"
    richiesta = urllib.request.Request(indirizzo, headers={"User-Agent": USER_AGENT, "X-Chiave-Ponte": chiave})
    return richiesta, f"{url} tramite il ponte"


def scarica(url: str, apri=urllib.request.urlopen, dormi=time.sleep, ambiente=os.environ) -> str:
    """Scarica un file e lo restituisce come testo.

    `apri`, `dormi` e `ambiente` si possono sostituire nei test, per non usare la rete,
    non aspettare davvero e decidere se c'è il ponte.
    """
    richiesta, descrizione = _richiesta(url, ambiente)
    ultimo_errore = None
    for tentativo in range(1, TENTATIVI + 1):
        try:
            with apri(richiesta, timeout=TIMEOUT_SECONDI) as risposta:
                if risposta.status != 200:
                    raise ErroreDownload(f"risposta HTTP {risposta.status}")
                corpo = risposta.read()
            break
        except (OSError, ErroreDownload) as errore:  # URLError, HTTPError e i timeout sono OSError
            ultimo_errore = errore
            if tentativo < TENTATIVI:
                dormi(PAUSA_SECONDI)
    else:
        raise ErroreDownload(f"download fallito dopo {TENTATIVI} tentativi: {descrizione} ({ultimo_errore})")

    # Il ponte risponde compresso con gzip (i file del MIMIT sono testo e non iniziano mai così)
    if corpo[:2] == b"\x1f\x8b":
        corpo = gzip.decompress(corpo)
    if not corpo:
        raise ErroreDownload(f"il file scaricato è vuoto: {descrizione}")
    try:
        return corpo.decode("utf-8")
    except UnicodeDecodeError as errore:
        raise FormatoNonValido(f"il file non è in UTF-8 come previsto: {descrizione} ({errore})") from errore
