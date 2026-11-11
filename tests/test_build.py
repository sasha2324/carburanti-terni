"""Test della costruzione del sito: formati italiani, grafico, pagine generate."""

import json

import pytest

from sito.build import costruisci
from sito.formato import comune_leggibile, data_breve, data_lunga, prezzo_parti, prezzo_testo
from sito.grafico import grafico_barre, grafico_linee

# --- formati ------------------------------------------------------------------


def test_prezzo_con_la_virgola_e_tre_decimali():
    assert prezzo_testo(1.989) == "1,989"
    assert prezzo_testo(2.0) == "2,000"


def test_prezzo_diviso_come_sui_cartelli_dei_distributori():
    """Sui cartelli la terza cifra decimale è scritta più piccola: 1,98⁹."""
    assert prezzo_parti(1.989) == ("1,98", "9")


def test_data_breve_in_italiano():
    assert data_breve("2026-11-09T20:00:07") == "9 nov, 20:00"


@pytest.mark.parametrize(
    "maiuscolo, leggibile",
    [
        ("TERNI", "Terni"),
        ("CALVI DELL'UMBRIA", "Calvi dell'Umbria"),
        ("MONTELEONE D'ORVIETO", "Monteleone d'Orvieto"),
        ("LUGNANO IN TEVERINA", "Lugnano in Teverina"),
        ("SAN GEMINI", "San Gemini"),
    ],
)
def test_nome_del_comune_leggibile(maiuscolo, leggibile):
    assert comune_leggibile(maiuscolo) == leggibile


def test_data_lunga_in_italiano():
    assert data_lunga("2026-11-10") == "martedì 10 novembre 2026"


# --- grafico ------------------------------------------------------------------

SERIE = {
    "self": [("2026-11-10", 1.99), ("2026-11-11", 1.97), ("2026-11-12", 1.98)],
    "servito": [("2026-11-10", 2.11), ("2026-11-11", 2.12), ("2026-11-12", 2.10)],
}


def test_il_grafico_ha_una_linea_per_serie():
    svg = grafico_linee(SERIE, titolo="Benzina")
    assert svg.startswith("<svg")
    assert svg.count('class="linea ') == 2


def test_il_grafico_con_un_solo_giorno_mostra_dei_punti():
    svg = grafico_linee({"self": [("2026-11-10", 1.99)]}, titolo="Benzina")
    assert 'class="linea ' not in svg
    assert 'class="punto ' in svg


def test_senza_dati_non_c_e_grafico():
    assert grafico_linee({}, titolo="Benzina") is None


def test_il_grafico_a_barre_ha_una_barra_per_giorno_e_evidenzia_il_piu_economico():
    centesimi = [-1.7, 0.3, 0.3, 0.3, 0.3, 0.3, 0.2]
    svg = grafico_barre(centesimi, ["lun", "mar", "mer", "gio", "ven", "sab", "dom"], titolo="Benzina self")
    assert svg.count('class="barra') == 7
    assert svg.count('class="barra evidenziata"') == 1


# --- costruzione completa -----------------------------------------------------


def file_del_giorno(estrazione, prezzo_1):
    impianto = {
        "nome": "",
        "gestore": "G",
        "bandiera": "Agip Eni",
        "tipo": "Stradale",
        "indirizzo": "VIA ROMA 1",
        "comune": "TERNI",
        "lat": 42.56,
        "lon": 12.64,
    }
    return {
        "estrazione": estrazione,
        "generato": f"{estrazione}T09:30:00+00:00",
        "impianti": [
            {
                **impianto,
                "id": 1,
                "nome": "ECONOMICO",
                "prezzi": [{"carburante": "Benzina", "self": True, "prezzo": prezzo_1, "comunicato": f"{estrazione}T07:00:00"}],
            },
            {
                **impianto,
                "id": 2,
                "nome": "CARO <B>",
                "prezzi": [{"carburante": "Benzina", "self": True, "prezzo": 2.099, "comunicato": f"{estrazione}T07:00:00"}],
            },
            {**impianto, "id": 3, "nome": "SENZA PREZZI", "lat": None, "lon": None, "prezzi": []},
        ],
        "scartati": [],
    }


@pytest.fixture
def sito(tmp_path):
    dati = tmp_path / "data"
    dati.mkdir()
    for estrazione, prezzo in [("2026-11-10", 1.959), ("2026-11-11", 1.949)]:
        (dati / f"{estrazione}.json").write_text(json.dumps(file_del_giorno(estrazione, prezzo)), encoding="utf-8")
    uscita = tmp_path / "dist"
    costruisci(dati, uscita)
    return uscita


def test_genera_tutte_le_pagine(sito):
    pagine = sorted(p.relative_to(sito).as_posix() for p in sito.rglob("*.html"))
    assert pagine == [
        "distributore/1.html",
        "distributore/2.html",
        "distributore/3.html",
        "giorno-della-settimana.html",
        "index.html",
        "mappa.html",
    ]


def test_ogni_pagina_cita_fonte_e_licenza(sito):
    for pagina in sito.rglob("*.html"):
        html = pagina.read_text(encoding="utf-8")
        assert "mimit.gov.it" in html, pagina
        assert "IODL 2.0" in html, pagina


def test_la_classifica_usa_l_ultimo_giorno_e_parte_dal_piu_economico(sito):
    html = (sito / "index.html").read_text(encoding="utf-8")
    assert html.index("ECONOMICO") < html.index("CARO")
    assert "1,94" in html  # prezzo dell'11 novembre, non del 10


def test_i_nomi_vengono_protetti_nell_html(sito):
    """Un nome con caratteri speciali non deve diventare codice HTML."""
    html = (sito / "distributore" / "2.html").read_text(encoding="utf-8")
    assert "CARO &lt;B&gt;" in html
    assert "CARO <B>" not in html


def test_copia_i_file_statici(sito):
    assert (sito / "static" / "style.css").exists()
    assert (sito / "static" / "vendor" / "leaflet" / "leaflet.js").exists()


def test_senza_file_di_dati_si_ferma(tmp_path):
    (tmp_path / "data").mkdir()
    with pytest.raises(FileNotFoundError, match="data"):
        costruisci(tmp_path / "data", tmp_path / "dist")
