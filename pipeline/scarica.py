"""Download dei file MIMIT, con tentativi ripetuti e messaggi d'errore chiari."""

import time
import urllib.error
import urllib.request

from pipeline.leggi import FormatoNonValido

URL_ANAGRAFICA = "https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv"
URL_PREZZI = "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"

USER_AGENT = "prezzi-carburanti-terni/0.1 (sito statico con open data MIMIT)"
TIMEOUT_SECONDI = 60
TENTATIVI = 3
PAUSA_SECONDI = 30


class ErroreDownload(Exception):
    """Il file non è arrivato: rete, server o risposta inattesa."""


def scarica(url: str, apri=urllib.request.urlopen, dormi=time.sleep) -> str:
    """Scarica un file e lo restituisce come testo.

    `apri` e `dormi` si possono sostituire nei test, per non usare la rete e non aspettare davvero.
    """
    ultimo_errore = None
    for tentativo in range(1, TENTATIVI + 1):
        try:
            richiesta = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with apri(richiesta, timeout=TIMEOUT_SECONDI) as risposta:
                if risposta.status != 200:
                    raise ErroreDownload(f"risposta HTTP {risposta.status}")
                corpo = risposta.read()
            break
        except (OSError, ErroreDownload) as errore:  # URLError e i timeout sono OSError
            ultimo_errore = errore
            if tentativo < TENTATIVI:
                dormi(PAUSA_SECONDI)
    else:
        raise ErroreDownload(f"download fallito dopo {TENTATIVI} tentativi: {url} ({ultimo_errore})")

    if not corpo:
        raise ErroreDownload(f"il file scaricato è vuoto: {url}")
    try:
        return corpo.decode("utf-8")
    except UnicodeDecodeError as errore:
        raise FormatoNonValido(f"il file non è in UTF-8 come previsto: {url} ({errore})") from errore
