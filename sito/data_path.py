"""The real numbers shown on the "Come funziona" page.

They are computed while the site is built, from the newest file in data/ and from
all the saved days: the visitor's browser downloads nothing extra.
"""

from collections import Counter

from sito.analisi import classifica

# The price signs of the petrol station in the 3D version: the cheapest self-service prices.
SIGNS = [("Benzina", True, "Benzina self"), ("Gasolio", True, "Gasolio self")]

# The reasons written by pipeline/pulisci.py, in the order of the cleaning rules,
# with the words shown on the page.
REASONS = [
    ("vecchio", "troppo vecchi"),
    ("fuori_scala", "fuori scala"),
    ("lontano_dalla_mediana", "probabili errori di battitura"),
    ("duplicato", "doppioni"),
]


def path_numbers(days: list[dict]) -> dict:
    """Numbers of the last run and totals over all saved days (days sorted by date)."""
    last = days[-1]
    removed = Counter(item["motivo"] for d in days for item in d["scartati"])

    by_reason = [(label, removed.pop(reason, 0)) for reason, label in REASONS]
    # A reason added to the cleaning later is still counted, with its own name.
    by_reason += sorted(removed.items())

    return {
        "date": last["estrazione"],
        "file": f"{last['estrazione']}.json",
        "generated": last["generato"],
        "stations": len(last["impianti"]),
        "stations_with_prices": sum(1 for s in last["impianti"] if s["prezzi"]),
        "prices": sum(len(s["prezzi"]) for s in last["impianti"]),
        "removed_last": len(last["scartati"]),
        "removed_total": sum(count for _, count in by_reason),
        "removed_by_reason": by_reason,
        "days": len(days),
        "first_day": days[0]["estrazione"],
        "cheapest": cheapest(last),
    }


def cheapest(day: dict) -> list[tuple[str, float]]:
    """The lowest price of each sign, from the same ranking as the home page."""
    signs = []
    for fuel, self_service, label in SIGNS:
        rows = classifica(day, fuel, self_service)
        if rows:
            signs.append((label, rows[0]["prezzo"]))
    return signs
