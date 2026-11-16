"""Tests for the numbers on the "Come funziona" page (sito/data_path.py)."""

from sito.data_path import path_numbers
from sito.formato import rome_time


def station(prices: int) -> dict:
    return {"id": 1, "prezzi": [{"carburante": "Benzina", "self": True, "prezzo": 1.9}] * prices}


def day(date: str, stations: list[dict], removed: list[str], generated: str = "2026-11-16T12:53:26+00:00") -> dict:
    return {
        "estrazione": date,
        "generato": generated,
        "impianti": stations,
        "scartati": [{"id": 1, "motivo": reason} for reason in removed],
    }


DAYS = [
    day("2026-04-01", [station(2)], ["vecchio", "vecchio"]),
    day("2026-04-02", [station(1)], ["fuori_scala"]),
    day("2026-11-15", [station(3), station(0), station(4)], ["vecchio"]),
]


def test_numbers_of_the_last_run():
    numbers = path_numbers(DAYS)
    assert numbers["date"] == "2026-11-15"
    assert numbers["file"] == "2026-11-15.json"
    assert numbers["generated"] == "2026-11-16T12:53:26+00:00"
    assert numbers["stations"] == 3
    assert numbers["stations_with_prices"] == 2
    assert numbers["prices"] == 7
    assert numbers["removed_last"] == 1


def test_totals_over_all_saved_days():
    numbers = path_numbers(DAYS)
    assert numbers["days"] == 3
    assert numbers["first_day"] == "2026-04-01"
    assert numbers["removed_total"] == 4


def test_removed_by_reason_in_a_fixed_order_with_zeros():
    """Every cleaning rule appears, also when it removed nothing: the page shows that it exists."""
    assert path_numbers(DAYS)["removed_by_reason"] == [
        ("troppo vecchi", 3),
        ("fuori scala", 1),
        ("probabili errori di battitura", 0),
        ("doppioni", 0),
    ]


def test_an_unknown_reason_is_counted_with_its_own_name():
    days = [day("2026-11-15", [station(1)], ["nuova_regola"])]
    assert ("nuova_regola", 1) in path_numbers(days)["removed_by_reason"]


def test_a_day_without_removed_prices():
    days = [day("2026-11-15", [station(1)], [])]
    numbers = path_numbers(days)
    assert numbers["removed_last"] == 0
    assert numbers["removed_total"] == 0


def test_rome_time_in_winter_is_utc_plus_one():
    assert rome_time("2026-11-16T12:53:26+00:00") == "16 nov, 13:53"


def test_rome_time_in_summer_is_utc_plus_two():
    assert rome_time("2026-07-01T06:00:00+00:00") == "1 lug, 08:00"
