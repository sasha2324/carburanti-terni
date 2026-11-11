"""Test della lettura dei file MIMIT: formato, intestazioni, righe sporche."""

from datetime import date, datetime

import pytest

from pipeline.leggi import FormatoNonValido, Impianto, Prezzo, leggi_anagrafica, leggi_prezzi

INTESTAZIONE_ANAGRAFICA = (
    "idImpianto|Gestore|Bandiera|Tipo Impianto|Nome Impianto|Indirizzo|Comune|Provincia|Latitudine|Longitudine"
)
INTESTAZIONE_PREZZI = "idImpianto|descCarburante|prezzo|isSelf|dtComu"
PRIMA_RIGA = "Estrazione del 2026-11-10"

RIGA_TERNI = "12345|ROSSI SRL|Agip Eni|Stradale|ROSSI TERNI|VIA ROMA 1 05100|TERNI|TR|42.56|12.64"
RIGA_PREZZO = "12345|Benzina|1.989|1|09/11/2026 20:00:07"


def anagrafica(*righe, prima=PRIMA_RIGA, intestazione=INTESTAZIONE_ANAGRAFICA):
    return "\n".join([prima, intestazione, *righe]) + "\n"


def prezzi(*righe, prima=PRIMA_RIGA, intestazione=INTESTAZIONE_PREZZI):
    return "\n".join([prima, intestazione, *righe]) + "\n"


def molti_impianti(quanti=200):
    return [f"{i}|G|B|Stradale|N|I|TERNI|TR|42.5|12.6" for i in range(1, quanti + 1)]


def molti_prezzi(quanti=200):
    return [f"{i}|Benzina|1.9|1|09/11/2026 20:00:07" for i in range(1, quanti + 1)]


# --- formato generale ---------------------------------------------------------


def test_legge_la_data_di_estrazione():
    assert leggi_anagrafica(anagrafica(RIGA_TERNI)).data == date(2026, 11, 10)


def test_prima_riga_inattesa_ferma_tutto():
    with pytest.raises(FormatoNonValido, match="prima riga"):
        leggi_anagrafica(anagrafica(RIGA_TERNI, prima="Export 10/11/2026"))


def test_data_impossibile_nella_prima_riga_ferma_tutto():
    with pytest.raises(FormatoNonValido, match="prima riga"):
        leggi_anagrafica(anagrafica(RIGA_TERNI, prima="Estrazione del 2026-13-45"))


def test_intestazione_cambiata_ferma_tutto():
    """È il caso del cambio di separatore: con ';' l'intestazione non coincide più."""
    vecchia = INTESTAZIONE_ANAGRAFICA.replace("|", ";")
    with pytest.raises(FormatoNonValido, match="intestazione"):
        leggi_anagrafica(anagrafica(RIGA_TERNI.replace("|", ";"), intestazione=vecchia))


def test_file_senza_righe_ferma_tutto():
    with pytest.raises(FormatoNonValido, match="nessuna riga"):
        leggi_anagrafica(anagrafica())


def test_troppe_righe_illeggibili_ferma_tutto():
    with pytest.raises(FormatoNonValido, match="illeggibili"):
        leggi_anagrafica(anagrafica(RIGA_TERNI, "riga|rotta"))


def test_tollera_il_bom_iniziale():
    letto = leggi_anagrafica("﻿" + anagrafica(RIGA_TERNI))
    assert letto.data == date(2026, 11, 10)


def test_tollera_le_fini_riga_windows():
    letto = leggi_anagrafica(anagrafica(RIGA_TERNI).replace("\n", "\r\n"))
    assert letto.righe[0].lon == 12.64


# --- anagrafica ---------------------------------------------------------------


def test_legge_i_campi_di_un_impianto():
    assert leggi_anagrafica(anagrafica(RIGA_TERNI)).righe == [
        Impianto(
            id=12345,
            gestore="ROSSI SRL",
            bandiera="Agip Eni",
            tipo="Stradale",
            nome="ROSSI TERNI",
            indirizzo="VIA ROMA 1 05100",
            comune="TERNI",
            provincia="TR",
            lat=42.56,
            lon=12.64,
        )
    ]


def test_toglie_spazi_doppi_e_tabulazioni():
    riga = "1|G|B|Stradale|19834\tMONTALLEGRO|SS.115  KM.158  |TERNI|TR|42.5|12.6"
    impianto = leggi_anagrafica(anagrafica(riga)).righe[0]
    assert impianto.nome == "19834 MONTALLEGRO"
    assert impianto.indirizzo == "SS.115 KM.158"


def test_recupera_la_riga_con_barra_verticale_nel_nome():
    riga = (
        "40820|STOIL SIMPLE|Pompe Bianche|Stradale|STOIL SIMPLE | gestori.prezzibenzina.it"
        "|STR. PROV.LE 82 15122|ALESSANDRIA|AL|44.917|8.7"
    )
    impianto = leggi_anagrafica(anagrafica(riga)).righe[0]
    assert impianto.nome == "STOIL SIMPLE | gestori.prezzibenzina.it"
    assert impianto.indirizzo == "STR. PROV.LE 82 15122"
    assert (impianto.comune, impianto.provincia, impianto.lat, impianto.lon) == ("ALESSANDRIA", "AL", 44.917, 8.7)


def test_coordinate_vuote_diventano_none():
    impianto = leggi_anagrafica(anagrafica("1|G|B|Stradale|N|I|TERNI|TR||")).righe[0]
    assert impianto.lat is None
    assert impianto.lon is None


def test_coordinate_non_numeriche_diventano_none_senza_scartare_l_impianto():
    letto = leggi_anagrafica(anagrafica("1|G|B|Stradale|N|I|TERNI|TR|n.d.|12,6"))
    assert (letto.righe[0].lat, letto.righe[0].lon) == (None, None)
    assert letto.illeggibili == 0


def test_salta_e_conta_la_riga_con_campi_mancanti():
    letto = leggi_anagrafica(anagrafica(*molti_impianti(200), "999|riga troncata"))
    assert len(letto.righe) == 200
    assert letto.illeggibili == 1


def test_salta_la_riga_con_identificativo_non_numerico():
    letto = leggi_anagrafica(anagrafica(*molti_impianti(200), "X1|G|B|Stradale|N|I|TERNI|TR|42.5|12.6"))
    assert letto.illeggibili == 1


# --- prezzi -------------------------------------------------------------------


def test_legge_i_campi_di_un_prezzo():
    assert leggi_prezzi(prezzi(RIGA_PREZZO)).righe == [
        Prezzo(
            id_impianto=12345,
            carburante="Benzina",
            prezzo=1.989,
            self_service=True,
            comunicato=datetime(2026, 11, 9, 20, 0, 7),
        )
    ]


def test_is_self_zero_vuol_dire_servito():
    prezzo = leggi_prezzi(prezzi("12345|Gasolio|2.329|0|09/11/2026 20:00:07")).righe[0]
    assert prezzo.self_service is False


def test_intestazione_prezzi_cambiata_ferma_tutto():
    with pytest.raises(FormatoNonValido, match="intestazione"):
        leggi_prezzi(prezzi(RIGA_PREZZO, intestazione=INTESTAZIONE_PREZZI + "|nuovaColonna"))


@pytest.mark.parametrize(
    "riga",
    [
        "12345|Benzina|1,989|1|09/11/2026 20:00:07",  # virgola al posto del punto
        "12345|Benzina|nan|1|09/11/2026 20:00:07",  # numero non finito
        "12345|Benzina|1.989|2|09/11/2026 20:00:07",  # isSelf diverso da 0/1
        "12345|Benzina|1.989|1|2026-11-09 20:00:07",  # data in un altro formato
        "abc|Benzina|1.989|1|09/11/2026 20:00:07",  # identificativo non numerico
        "12345|Benzina|1.989|1",  # campo mancante
    ],
)
def test_riga_prezzo_non_valida_viene_scartata(riga):
    letto = leggi_prezzi(prezzi(*molti_prezzi(200), riga))
    assert len(letto.righe) == 200
    assert letto.illeggibili == 1
