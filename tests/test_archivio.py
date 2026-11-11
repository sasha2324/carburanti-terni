"""Test dell'importazione dello storico dall'archivio trimestrale del MIMIT."""

import io
import json
import tarfile
from datetime import date, datetime, timezone

from pipeline.archivio import importa
from pipeline.leggi import Impianto, Letto

ADESSO = datetime(2026, 11, 11, 10, 0, tzinfo=timezone.utc)
INTESTAZIONE = "idImpianto|descCarburante|prezzo|isSelf|dtComu"


def anagrafica_di_terni(quanti=35):
    impianti = [
        Impianto(
            id=i,
            gestore="G",
            bandiera="B",
            tipo="Stradale",
            nome=f"Impianto {i}",
            indirizzo="VIA ROMA 1",
            comune="TERNI",
            provincia="TR",
            lat=42.56,
            lon=12.64,
        )
        for i in range(1, quanti + 1)
    ]
    return Letto(data=date(2026, 11, 10), righe=impianti, illeggibili=0)


def giorno_csv(estrazione, prezzo=1.9, intestazione=INTESTAZIONE):
    giorno, mese, anno = estrazione[8:10], estrazione[5:7], estrazione[:4]
    righe = [f"{i}|Benzina|{prezzo}|1|{giorno}/{mese}/{anno} 07:00:00" for i in range(1, 36)]
    return "\n".join([f"Estrazione del {estrazione}", intestazione, *righe])


def archivio(cartella, voci):
    """Crea un .tar.gz come quelli del MIMIT. `voci` è {nome: testo}; testo None = cartella."""
    percorso = cartella / "2026_3_tr.tar.gz"
    with tarfile.open(percorso, "w:gz") as tar:
        for nome, testo in voci.items():
            info = tarfile.TarInfo(nome)
            if testo is None:
                info.type = tarfile.DIRTYPE
                tar.addfile(info)
            else:
                dati = testo.encode("utf-8")
                info.size = len(dati)
                tar.addfile(info, io.BytesIO(dati))
    return percorso


def test_salva_un_file_per_ogni_giorno_dell_archivio(tmp_path):
    dati = tmp_path / "data"
    tar = archivio(
        tmp_path,
        {
            "./2026_3_tr/prezzo_alle_8-20260701.csv": giorno_csv("2026-07-01"),
            "./2026_3_tr/prezzo_alle_8-20260702.csv": giorno_csv("2026-07-02"),
        },
    )
    esito = importa([tar], anagrafica_di_terni(), dati, adesso=ADESSO)
    assert esito.salvati == ["2026-07-01", "2026-07-02"]
    contenuto = json.loads((dati / "2026-07-01.json").read_text(encoding="utf-8"))
    assert contenuto["estrazione"] == "2026-07-01"
    assert contenuto["fonte"] == "archivio MIMIT, anagrafica del 2026-11-10"
    assert len(contenuto["impianti"]) == 35


def test_non_tocca_i_giorni_gia_salvati(tmp_path):
    dati = tmp_path / "data"
    dati.mkdir()
    (dati / "2026-07-01.json").write_text("già salvato", encoding="utf-8")
    tar = archivio(tmp_path, {"prezzo_alle_8-20260701.csv": giorno_csv("2026-07-01")})
    esito = importa([tar], anagrafica_di_terni(), dati, adesso=ADESSO)
    assert esito.gia_presenti == ["2026-07-01"]
    assert (dati / "2026-07-01.json").read_text(encoding="utf-8") == "già salvato"


def test_un_giorno_illeggibile_viene_saltato_e_segnalato(tmp_path):
    dati = tmp_path / "data"
    tar = archivio(
        tmp_path,
        {
            "prezzo_alle_8-20260701.csv": giorno_csv("2026-07-01", intestazione=INTESTAZIONE.replace("|", ";")),
            "prezzo_alle_8-20260702.csv": giorno_csv("2026-07-02"),
        },
    )
    esito = importa([tar], anagrafica_di_terni(), dati, adesso=ADESSO)
    assert esito.salvati == ["2026-07-02"]
    assert [nome for nome, _ in esito.saltati] == ["prezzo_alle_8-20260701.csv"]
    assert "intestazione" in esito.saltati[0][1]
    assert not (dati / "2026-07-01.json").exists()


def test_ignora_le_voci_che_non_sono_file_dei_prezzi(tmp_path):
    tar = archivio(
        tmp_path,
        {
            "./2026_3_tr/": None,
            "./2026_3_tr/LEGGIMI.txt": "non sono un CSV",
            "./2026_3_tr/prezzo_alle_8-20260701.csv": giorno_csv("2026-07-01"),
        },
    )
    esito = importa([tar], anagrafica_di_terni(), tmp_path / "data", adesso=ADESSO)
    assert esito.salvati == ["2026-07-01"]
    assert esito.saltati == []
