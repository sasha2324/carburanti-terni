"""Test della pulizia: filtro Terni, unione, prezzi vecchi, fuori scala, coordinate."""

import json
from datetime import date, datetime

import pytest

from pipeline.leggi import Impianto, Letto, Prezzo
from pipeline.pulisci import DatiNonPlausibili, pulisci

ESTRAZIONE = date(2026, 11, 10)
IERI_SERA = datetime(2026, 11, 9, 20, 0, 0)


def impianto(id, provincia="TR", lat=42.56, lon=12.64):
    return Impianto(
        id=id,
        gestore="G",
        bandiera="B",
        tipo="Stradale",
        nome=f"Impianto {id}",
        indirizzo="VIA ROMA 1",
        comune="TERNI",
        provincia=provincia,
        lat=lat,
        lon=lon,
    )


def prezzo(id, valore=1.989, carburante="Benzina", self_service=True, comunicato=IERI_SERA):
    return Prezzo(
        id_impianto=id, carburante=carburante, prezzo=valore, self_service=self_service, comunicato=comunicato
    )


def esegui(impianti, prezzi, data_anagrafica=ESTRAZIONE, data_prezzi=ESTRAZIONE, minimo_impianti=1):
    return pulisci(
        Letto(data=data_anagrafica, righe=impianti, illeggibili=0),
        Letto(data=data_prezzi, righe=prezzi, illeggibili=0),
        minimo_impianti=minimo_impianti,
    )


def prezzi_di(risultato, id):
    return next(i["prezzi"] for i in risultato["impianti"] if i["id"] == id)


def valori_di(risultato, id):
    return [p["prezzo"] for p in prezzi_di(risultato, id)]


def motivi(risultato):
    return [(s["id"], s["prezzo"], s["motivo"]) for s in risultato["scartati"]]


# --- filtro e unione ----------------------------------------------------------


def test_tiene_solo_gli_impianti_della_provincia_di_terni():
    risultato = esegui([impianto(1), impianto(2, provincia="PG")], [])
    assert [i["id"] for i in risultato["impianti"]] == [1]


def test_collega_i_prezzi_all_impianto_giusto_tramite_identificativo():
    risultato = esegui(
        [impianto(1), impianto(2), impianto(3, provincia="PG")],
        [prezzo(1, 1.901), prezzo(2, 1.902), prezzo(3, 1.903)],
    )
    assert valori_di(risultato, 1) == [1.901]
    assert valori_di(risultato, 2) == [1.902]
    assert risultato["scartati"] == []


def test_impianto_senza_prezzi_resta_con_lista_vuota():
    assert prezzi_di(esegui([impianto(1)], []), 1) == []


# --- prezzi vecchi ------------------------------------------------------------


def test_prezzo_comunicato_7_giorni_prima_dell_estrazione_resta():
    risultato = esegui([impianto(1)], [prezzo(1, comunicato=datetime(2026, 11, 3, 7, 0))])
    assert valori_di(risultato, 1) == [1.989]


def test_prezzo_comunicato_8_giorni_prima_dell_estrazione_e_vecchio():
    risultato = esegui([impianto(1)], [prezzo(1, comunicato=datetime(2026, 11, 2, 23, 59))])
    assert valori_di(risultato, 1) == []
    assert motivi(risultato) == [(1, 1.989, "vecchio")]


# --- fuori scala --------------------------------------------------------------


@pytest.mark.parametrize("valore", [0.1, 8.888])
def test_prezzo_fuori_dai_limiti_assoluti_viene_scartato(valore):
    risultato = esegui([impianto(1)], [prezzo(1, valore)])
    assert motivi(risultato) == [(1, valore, "fuori_scala")]


def test_gpl_a_55_centesimi_non_e_fuori_scala():
    risultato = esegui([impianto(1)], [prezzo(1, 0.549, carburante="GPL")])
    assert valori_di(risultato, 1) == [0.549]


def test_prezzo_lontano_piu_del_25_per_cento_dalla_mediana_viene_scartato():
    """L'errore di battitura tipico: 1,199 al posto di 2,199."""
    normali = [prezzo(i, 2.199) for i in range(1, 6)]
    risultato = esegui([impianto(i) for i in range(1, 7)], [*normali, prezzo(6, 1.199)])
    assert motivi(risultato) == [(6, 1.199, "lontano_dalla_mediana")]


def test_prezzo_lontano_meno_del_25_per_cento_dalla_mediana_resta():
    normali = [prezzo(i, 2.0) for i in range(1, 6)]
    risultato = esegui([impianto(i) for i in range(1, 7)], [*normali, prezzo(6, 2.49)])
    assert valori_di(risultato, 6) == [2.49]


def test_self_e_servito_hanno_mediane_separate():
    """Il servito costa di più: se si mescolassero, i serviti sembrerebbero errori."""
    self_service = [prezzo(i, 1.5, self_service=True) for i in range(1, 7)]
    servito = [prezzo(i, 2.3, self_service=False) for i in range(1, 6)]
    risultato = esegui([impianto(i) for i in range(1, 7)], [*self_service, *servito])
    assert risultato["scartati"] == []


def test_carburanti_diversi_hanno_mediane_separate():
    benzina = [prezzo(i, 2.0, carburante="Benzina") for i in range(1, 7)]
    metano = [prezzo(i, 1.4, carburante="Metano") for i in range(1, 6)]
    risultato = esegui([impianto(i) for i in range(1, 7)], [*benzina, *metano])
    assert risultato["scartati"] == []


def test_con_meno_di_5_prezzi_la_mediana_non_si_usa():
    gpl = [prezzo(i, 0.6, carburante="GPL") for i in range(1, 4)]
    risultato = esegui([impianto(i) for i in range(1, 5)], [*gpl, prezzo(4, 0.95, carburante="GPL")])
    assert valori_di(risultato, 4) == [0.95]


def test_i_prezzi_vecchi_non_contano_per_la_mediana():
    """Cinque prezzi vecchi a 1,5 non devono far sembrare sbagliato quello fresco a 2,0."""
    vecchi = [prezzo(i, 1.5, comunicato=datetime(2026, 9, 1)) for i in range(1, 6)]
    risultato = esegui([impianto(i) for i in range(1, 7)], [*vecchi, prezzo(6, 2.0)])
    assert valori_di(risultato, 6) == [2.0]


# --- duplicati ----------------------------------------------------------------


def test_con_due_prezzi_uguali_per_carburante_e_modalita_tiene_il_piu_recente():
    risultato = esegui(
        [impianto(1)],
        [prezzo(1, 1.95, comunicato=datetime(2026, 11, 8)), prezzo(1, 1.97, comunicato=datetime(2026, 11, 9))],
    )
    assert valori_di(risultato, 1) == [1.97]
    assert motivi(risultato) == [(1, 1.95, "duplicato")]


# --- coordinate ---------------------------------------------------------------


@pytest.mark.parametrize("lat, lon", [(44.917, 8.7), (0.0, 0.0), (None, None), (42.56, None)])
def test_coordinate_non_plausibili_diventano_null_ma_l_impianto_resta(lat, lon):
    risultato = esegui([impianto(1, lat=lat, lon=lon)], [prezzo(1)])
    assert (risultato["impianti"][0]["lat"], risultato["impianti"][0]["lon"]) == (None, None)
    assert valori_di(risultato, 1) == [1.989]


def test_coordinate_dentro_la_provincia_restano():
    risultato = esegui([impianto(1, lat=42.56, lon=12.64)], [])
    assert (risultato["impianti"][0]["lat"], risultato["impianti"][0]["lon"]) == (42.56, 12.64)


# --- controlli che fermano tutto ----------------------------------------------


def test_date_di_estrazione_diverse_fermano_tutto():
    with pytest.raises(DatiNonPlausibili, match="date di estrazione"):
        esegui([impianto(1)], [], data_prezzi=date(2026, 11, 9))


def test_troppo_pochi_impianti_a_terni_fermano_tutto():
    with pytest.raises(DatiNonPlausibili, match="impianti"):
        esegui([impianto(1), impianto(2)], [], minimo_impianti=80)


# --- forma del risultato ------------------------------------------------------


def test_il_risultato_e_pronto_per_il_json():
    risultato = esegui([impianto(1)], [prezzo(1)])
    assert json.loads(json.dumps(risultato)) == {
        "estrazione": "2026-11-10",
        "impianti": [
            {
                "id": 1,
                "nome": "Impianto 1",
                "gestore": "G",
                "bandiera": "B",
                "tipo": "Stradale",
                "indirizzo": "VIA ROMA 1",
                "comune": "TERNI",
                "lat": 42.56,
                "lon": 12.64,
                "prezzi": [
                    {"carburante": "Benzina", "self": True, "prezzo": 1.989, "comunicato": "2026-11-09T20:00:00"}
                ],
            }
        ],
        "scartati": [],
    }
