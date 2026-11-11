"""Test della pipeline completa: cosa viene salvato e, soprattutto, quando NON si salva niente."""

import json
from datetime import datetime, timezone

import pytest

from pipeline.aggiorna import NessunDatoNuovo, aggiorna
from pipeline.leggi import FormatoNonValido
from pipeline.scarica import URL_ANAGRAFICA, URL_PREZZI

ADESSO = datetime(2026, 11, 11, 9, 30, tzinfo=timezone.utc)


def file_mimit(data="2026-11-10", intestazione_prezzi="idImpianto|descCarburante|prezzo|isSelf|dtComu"):
    impianti = [f"{i}|G|B|Stradale|N{i}|VIA ROMA {i}|TERNI|TR|42.56|12.64" for i in range(1, 101)]
    prezzi = [f"{i}|Benzina|1.989|1|09/11/2026 20:00:07" for i in range(1, 101)]
    return {
        URL_ANAGRAFICA: "\n".join(
            [
                f"Estrazione del {data}",
                "idImpianto|Gestore|Bandiera|Tipo Impianto|Nome Impianto|Indirizzo|Comune|Provincia|Latitudine|Longitudine",
                *impianti,
            ]
        ),
        URL_PREZZI: "\n".join([f"Estrazione del {data}", intestazione_prezzi, *prezzi]),
    }


def esegui(cartella, file):
    return aggiorna(cartella, scarica_testo=file.__getitem__, adesso=ADESSO)


def test_salva_il_file_con_la_data_di_estrazione_nel_nome(tmp_path):
    percorso = esegui(tmp_path, file_mimit())
    assert percorso == tmp_path / "2026-11-10.json"
    contenuto = json.loads(percorso.read_text(encoding="utf-8"))
    assert contenuto["estrazione"] == "2026-11-10"
    assert contenuto["generato"] == "2026-11-11T09:30:00+00:00"
    assert len(contenuto["impianti"]) == 100


def test_se_la_data_e_gia_salvata_si_ferma_e_non_tocca_il_file(tmp_path):
    esistente = tmp_path / "2026-11-10.json"
    esistente.write_text("già salvato", encoding="utf-8")
    with pytest.raises(NessunDatoNuovo, match="2026-11-10"):
        esegui(tmp_path, file_mimit())
    assert esistente.read_text(encoding="utf-8") == "già salvato"


def test_con_un_formato_cambiato_non_salva_niente(tmp_path):
    with pytest.raises(FormatoNonValido):
        esegui(tmp_path, file_mimit(intestazione_prezzi="idImpianto;descCarburante;prezzo;isSelf;dtComu"))
    assert list(tmp_path.iterdir()) == []
