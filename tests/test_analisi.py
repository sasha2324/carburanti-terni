"""Test dei calcoli del sito: classifica, storico, giorno della settimana."""

from datetime import date, timedelta

import pytest

from sito.analisi import classifica, giorno_della_settimana, storico

LUNEDI = date(2026, 11, 2)  # un lunedì


def giorno(data, prezzi, comunicato="2026-11-09T20:00:00"):
    """Un file del giorno ridotto all'osso. `prezzi` è {id: {(carburante, self): prezzo}}."""
    return {
        "estrazione": data.isoformat() if isinstance(data, date) else data,
        "impianti": [
            {
                "id": id,
                "nome": f"Impianto {id}",
                "comune": "TERNI",
                "prezzi": [
                    {"carburante": c, "self": s, "prezzo": p, "comunicato": comunicato}
                    for (c, s), p in per_impianto.items()
                ],
            }
            for id, per_impianto in prezzi.items()
        ],
    }


# --- classifica ---------------------------------------------------------------


def test_classifica_dal_piu_economico():
    oggi = giorno("2026-11-10", {1: {("Benzina", True): 1.99}, 2: {("Benzina", True): 1.95}, 3: {("Benzina", True): 2.05}})
    assert [r["impianto"]["id"] for r in classifica(oggi, "Benzina", True)] == [2, 1, 3]


def test_classifica_considera_solo_carburante_e_modalita_richiesti():
    oggi = giorno(
        "2026-11-10",
        {1: {("Benzina", True): 1.99, ("Benzina", False): 1.80, ("Gasolio", True): 1.70}, 2: {("Benzina", True): 2.0}},
    )
    assert [(r["impianto"]["id"], r["prezzo"]) for r in classifica(oggi, "Benzina", True)] == [(1, 1.99), (2, 2.0)]


def test_a_parita_di_prezzo_prima_il_comunicato_piu_recente():
    oggi = giorno("2026-11-10", {})
    for id, comunicato in [(1, "2026-11-08T10:00:00"), (2, "2026-11-09T10:00:00")]:
        oggi["impianti"].append(
            {"id": id, "nome": f"I{id}", "prezzi": [{"carburante": "Benzina", "self": True, "prezzo": 1.99, "comunicato": comunicato}]}
        )
    assert [r["impianto"]["id"] for r in classifica(oggi, "Benzina", True)] == [2, 1]


def test_impianti_senza_quel_prezzo_non_compaiono():
    oggi = giorno("2026-11-10", {1: {("Gasolio", True): 2.2}, 2: {}})
    assert classifica(oggi, "Benzina", True) == []


# --- storico ------------------------------------------------------------------


def test_storico_raccoglie_i_prezzi_per_impianto_e_categoria_in_ordine_di_data():
    giorni = [
        giorno("2026-11-11", {1: {("Benzina", True): 1.97}}),
        giorno("2026-11-10", {1: {("Benzina", True): 1.99, ("Gasolio", False): 2.3}}),
    ]
    assert storico(giorni) == {
        1: {
            ("Benzina", True): [("2026-11-10", 1.99), ("2026-11-11", 1.97)],
            ("Gasolio", False): [("2026-11-10", 2.3)],
        }
    }


# --- giorno della settimana ---------------------------------------------------


def giorni_consecutivi(quanti, prezzo_del_giorno, impianti=(1,)):
    """`prezzo_del_giorno(id, data)` restituisce il prezzo di Benzina self, o None se manca."""
    risultato = []
    for n in range(quanti):
        data = LUNEDI + timedelta(days=n)
        prezzi = {}
        for id in impianti:
            valore = prezzo_del_giorno(id, data)
            prezzi[id] = {} if valore is None else {("Benzina", True): valore}
        risultato.append(giorno(data, prezzi))
    return risultato


def test_con_meno_di_8_settimane_non_e_pronto_e_dice_quanto_manca():
    analisi = giorno_della_settimana(giorni_consecutivi(10, lambda id, d: 2.0))
    assert analisi["pronto"] is False
    assert analisi["giorni_raccolti"] == 10
    assert analisi["giorni_mancanti"] == 46
    assert analisi["data_prevista"] == "2026-12-27"  # l'ultimo giorno dell'ottava settimana


def test_con_8_settimane_trova_il_giorno_piu_economico():
    """Il lunedì costa 2 centesimi in meno: rispetto alla media della settimana è -1,71 centesimi."""
    analisi = giorno_della_settimana(giorni_consecutivi(56, lambda id, d: 1.98 if d.weekday() == 0 else 2.0))
    assert analisi["pronto"] is True
    benzina_self = analisi["categorie"]["Benzina self"]
    assert benzina_self["piu_economico"] == 0  # lunedì
    assert benzina_self["centesimi"][0] == pytest.approx(-1.714, abs=0.001)
    assert benzina_self["centesimi"][3] == pytest.approx(0.286, abs=0.001)
    assert benzina_self["scarto_massimo"] == pytest.approx(2.0)  # tra il giorno più caro e il più economico


def test_un_distributore_presente_solo_nei_feriali_non_falsa_il_risultato():
    """Prezzi sempre costanti: nessun giorno deve risultare più conveniente,
    anche se il distributore economico (2) manca il sabato e la domenica."""

    def prezzo(id, data):
        if id == 2 and data.weekday() >= 5:
            return None
        return 2.0 if id == 1 else 1.8

    analisi = giorno_della_settimana(giorni_consecutivi(56, prezzo, impianti=(1, 2)))
    assert analisi["categorie"]["Benzina self"]["centesimi"] == pytest.approx([0.0] * 7)


def test_un_prezzo_in_salita_costante_non_fa_sembrare_conveniente_nessun_giorno():
    """Se i prezzi salgono ogni giorno un po', la domenica non deve sembrare più cara
    solo perché viene dopo il lunedì: conta il giorno, non la tendenza."""
    analisi = giorni_consecutivi(70, lambda id, d: 1.80 + 0.001 * (d - LUNEDI).days)
    risultato = giorno_della_settimana(analisi)
    assert risultato["categorie"]["Benzina self"]["centesimi"] == pytest.approx([0.0] * 7, abs=1e-9)


def test_le_finestre_incomplete_non_contano():
    """Il distributore 2 ha solo il lunedì (molto basso) di ogni settimana: va ignorato."""

    def prezzo(id, data):
        if id == 2:
            return 1.5 if data.weekday() == 0 else None
        return 2.0

    analisi = giorno_della_settimana(giorni_consecutivi(56, prezzo, impianti=(1, 2)))
    assert analisi["categorie"]["Benzina self"]["centesimi"] == pytest.approx([0.0] * 7)
