"""Test del download, senza internet: al posto della connessione vera si passa una finta."""

import urllib.error

import pytest

from pipeline.leggi import FormatoNonValido
from pipeline.scarica import ErroreDownload, scarica

URL = "https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv"


class RispostaFinta:
    def __init__(self, corpo: bytes, status: int = 200):
        self.corpo, self.status = corpo, status

    def read(self):
        return self.corpo

    def __enter__(self):
        return self

    def __exit__(self, *errore):
        return False


def connessione_finta(*risposte):
    """Restituisce una funzione che, a ogni chiamata, dà la risposta successiva (o solleva l'errore)."""
    chiamate = []

    def apri(richiesta, timeout):
        chiamate.append(richiesta.full_url)
        risposta = risposte[len(chiamate) - 1]
        if isinstance(risposta, Exception):
            raise risposta
        return risposta

    apri.chiamate = chiamate
    return apri


def scarica_con(*risposte):
    apri = connessione_finta(*risposte)
    return scarica(URL, apri=apri, dormi=lambda secondi: None), apri.chiamate


def test_restituisce_il_testo_del_file():
    testo, _ = scarica_con(RispostaFinta("Estrazione del 2026-11-10\nàè".encode()))
    assert testo == "Estrazione del 2026-11-10\nàè"


def test_dopo_un_errore_di_rete_riprova():
    testo, chiamate = scarica_con(urllib.error.URLError("rete giù"), RispostaFinta(b"ok"))
    assert testo == "ok"
    assert len(chiamate) == 2


def test_dopo_tre_errori_si_ferma_con_un_messaggio_chiaro():
    errore = urllib.error.URLError("rete giù")
    with pytest.raises(ErroreDownload, match="3 tentativi") as info:
        scarica_con(errore, errore, errore)
    assert URL in str(info.value)


def test_una_risposta_diversa_da_200_e_un_errore():
    with pytest.raises(ErroreDownload, match="HTTP 204"):
        scarica_con(RispostaFinta(b"", 204), RispostaFinta(b"", 204), RispostaFinta(b"", 204))


def test_un_file_vuoto_e_un_errore():
    with pytest.raises(ErroreDownload, match="vuoto"):
        scarica_con(RispostaFinta(b""))


def test_un_file_che_non_e_utf8_ferma_tutto():
    with pytest.raises(FormatoNonValido, match="UTF-8"):
        scarica_con(RispostaFinta("Estrazione àè".encode("latin-1")))


# --- Il ponte in Europa (vedi ponte/): il MIMIT non risponde ai server di GitHub, che sono negli USA ---

import gzip

from pipeline.scarica import URL_ANAGRAFICA, URL_PREZZI

PONTE = {"MIMIT_PONTE_URL": "https://ponte.example/", "MIMIT_PONTE_CHIAVE": "segreta"}


def scarica_dal_ponte(url, *risposte, ambiente=PONTE):
    richieste = []

    def apri(richiesta, timeout):
        richieste.append(richiesta)
        risposta = risposte[len(richieste) - 1]
        if isinstance(risposta, Exception):
            raise risposta
        return risposta

    testo = scarica(url, apri=apri, dormi=lambda secondi: None, ambiente=ambiente)
    return testo, richieste


def test_senza_ponte_scarica_dal_mimit_senza_chiave():
    _, richieste = scarica_dal_ponte(URL_PREZZI, RispostaFinta(b"ok"), ambiente={})
    assert richieste[0].full_url == URL_PREZZI
    assert richieste[0].get_header("X-chiave-ponte") is None


def test_con_il_ponte_chiede_il_file_giusto_con_la_chiave():
    _, richieste = scarica_dal_ponte(URL_ANAGRAFICA, RispostaFinta(b"ok"))
    assert richieste[0].full_url == "https://ponte.example/?file=anagrafica"
    assert richieste[0].get_header("X-chiave-ponte") == "segreta"
    _, richieste = scarica_dal_ponte(URL_PREZZI, RispostaFinta(b"ok"))
    assert richieste[0].full_url == "https://ponte.example/?file=prezzi"


def test_il_ponte_risponde_compresso_e_arriva_il_testo_in_chiaro():
    compresso = gzip.compress("Estrazione del 2026-11-16\nàè".encode())
    testo, _ = scarica_dal_ponte(URL_PREZZI, RispostaFinta(compresso))
    assert testo == "Estrazione del 2026-11-16\nàè"


def test_il_ponte_conosce_solo_i_due_file_del_mimit():
    with pytest.raises(ErroreDownload, match="ponte"):
        scarica_dal_ponte("https://altro.example/file.csv", RispostaFinta(b"ok"))


def test_se_il_ponte_fallisce_il_messaggio_lo_dice():
    errore = urllib.error.HTTPError("https://ponte.example/?file=prezzi", 403, "Forbidden", {}, None)
    with pytest.raises(ErroreDownload, match="tramite il ponte"):
        scarica_dal_ponte(URL_PREZZI, errore, errore, errore)
