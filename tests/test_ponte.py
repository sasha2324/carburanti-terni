"""Test del ponte in Europa (ponte/lambda_function.py), senza internet e senza AWS."""

import base64
import gzip
import urllib.error

from pipeline import scarica as pipeline_scarica
from ponte import lambda_function as ponte

CHIAVE = {"CHIAVE_PONTE": "segreta"}


class RispostaFinta:
    def __init__(self, corpo: bytes, status: int = 200):
        self.corpo, self.status = corpo, status

    def read(self):
        return self.corpo

    def __enter__(self):
        return self

    def __exit__(self, *errore):
        return False


def evento(file=None, chiave="segreta"):
    return {
        "headers": {"x-chiave-ponte": chiave} if chiave is not None else {},
        "queryStringParameters": {"file": file} if file else None,
    }


def chiama(ev, risposta=RispostaFinta(b"Estrazione del 2026-11-16\n"), ambiente=CHIAVE):
    chiesti = []

    def apri(richiesta, timeout):
        chiesti.append(richiesta.full_url)
        if isinstance(risposta, Exception):
            raise risposta
        return risposta

    return ponte.lambda_handler(ev, None, apri=apri, ambiente=ambiente), chiesti


def test_gli_indirizzi_sono_gli_stessi_della_pipeline():
    assert ponte.FILE == {"anagrafica": pipeline_scarica.URL_ANAGRAFICA, "prezzi": pipeline_scarica.URL_PREZZI}


def test_con_la_chiave_giusta_restituisce_il_file_compresso():
    risposta, chiesti = chiama(evento("prezzi"))
    assert risposta["statusCode"] == 200
    assert risposta["isBase64Encoded"] is True
    assert gzip.decompress(base64.b64decode(risposta["body"])) == b"Estrazione del 2026-11-16\n"
    assert chiesti == [pipeline_scarica.URL_PREZZI]


def test_senza_chiave_o_con_quella_sbagliata_rifiuta_senza_scaricare():
    for ev in (evento("prezzi", chiave=None), evento("prezzi", chiave="sbagliata")):
        risposta, chiesti = chiama(ev)
        assert risposta["statusCode"] == 403
        assert chiesti == []


def test_se_la_chiave_non_e_configurata_rifiuta_tutto():
    risposta, chiesti = chiama(evento("prezzi", chiave=""), ambiente={})
    assert risposta["statusCode"] == 403
    assert chiesti == []


def test_un_file_sconosciuto_non_viene_scaricato():
    for ev in (evento("altro"), evento(None)):
        risposta, chiesti = chiama(ev)
        assert risposta["statusCode"] == 404
        assert chiesti == []


def test_la_chiave_vale_anche_con_le_maiuscole_nel_nome_dell_intestazione():
    ev = evento("anagrafica")
    ev["headers"] = {"X-Chiave-Ponte": "segreta"}
    risposta, _ = chiama(ev)
    assert risposta["statusCode"] == 200


def test_se_il_mimit_non_risponde_restituisce_504_con_il_motivo():
    risposta, _ = chiama(evento("prezzi"), risposta=urllib.error.URLError("timed out"))
    assert risposta["statusCode"] == 504
    assert "MIMIT" in risposta["body"]


def test_se_il_mimit_risponde_male_restituisce_502():
    risposta, _ = chiama(evento("prezzi"), risposta=RispostaFinta(b"", status=500))
    assert risposta["statusCode"] == 502
