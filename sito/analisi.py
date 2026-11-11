"""Calcoli per il sito: classifica, storico, giorno della settimana.

Lavorano sui file del giorno di data/ (vedi docs/progetto.md, sezione 3) e non sanno niente di HTML.
"""

from collections import defaultdict
from datetime import date, timedelta

# Le quattro classifiche del sito: (carburante, self, etichetta)
CATEGORIE = [
    ("Benzina", True, "Benzina self"),
    ("Benzina", False, "Benzina servito"),
    ("Gasolio", True, "Gasolio self"),
    ("Gasolio", False, "Gasolio servito"),
]

SETTIMANE_MINIME = 8


def classifica(giorno: dict, carburante: str, self_service: bool) -> list[dict]:
    """Gli impianti che hanno quel prezzo, dal più economico.

    A parità di prezzo viene prima chi l'ha comunicato più di recente (è il dato più affidabile).
    """
    righe = [
        {"impianto": impianto, "prezzo": p["prezzo"], "comunicato": p["comunicato"]}
        for impianto in giorno["impianti"]
        for p in impianto["prezzi"]
        if p["carburante"] == carburante and p["self"] == self_service
    ]
    # Python ordina in modo "stabile": ordinando prima per data e poi per prezzo,
    # a parità di prezzo resta l'ordine per data.
    righe.sort(key=lambda r: r["comunicato"], reverse=True)
    righe.sort(key=lambda r: r["prezzo"])
    return righe


def storico(giorni: list[dict]) -> dict[int, dict[tuple[str, bool], list[tuple[str, float]]]]:
    """Per ogni impianto e (carburante, self): la lista (data di estrazione, prezzo) in ordine di data."""
    risultato = defaultdict(lambda: defaultdict(list))
    for giorno in sorted(giorni, key=lambda g: g["estrazione"]):
        for impianto in giorno["impianti"]:
            for p in impianto["prezzi"]:
                risultato[impianto["id"]][(p["carburante"], p["self"])].append((giorno["estrazione"], p["prezzo"]))
    return {id: dict(per_categoria) for id, per_categoria in risultato.items()}


def giorno_della_settimana(giorni: list[dict]) -> dict:
    """Quale giorno della settimana conviene, se lo storico basta.

    Metodo: per ogni distributore si confronta il prezzo di ogni giorno con la media dei 7 giorni
    centrati su quel giorno, nello stesso distributore; poi si fa la media di questi scarti per
    giorno della settimana. Così non conta quali distributori entrano o escono dai dati, e una
    tendenza generale (prezzi in salita o in discesa) non fa sembrare più cari gli ultimi giorni.
    """
    date_raccolte = sorted({date.fromisoformat(g["estrazione"]) for g in giorni})
    per_giorno = [0] * 7
    for d in date_raccolte:
        per_giorno[d.weekday()] += 1

    ultima = date_raccolte[-1] if date_raccolte else None
    mancanti = _giorni_mancanti(per_giorno, ultima)
    risultato = {
        "pronto": mancanti == 0,
        "giorni_raccolti": len(date_raccolte),
        "giorni_mancanti": mancanti,
        "data_prevista": (ultima + timedelta(days=mancanti)).isoformat() if ultima else None,
        "settimane_minime": SETTIMANE_MINIME,
        "categorie": {},
    }
    if not risultato["pronto"]:
        return risultato

    serie = storico(giorni)
    for carburante, self_service, etichetta in CATEGORIE:
        scarti = [[] for _ in range(7)]
        for per_categoria in serie.values():
            prezzi = {date.fromisoformat(d): p for d, p in per_categoria.get((carburante, self_service), [])}
            for giorno, prezzo in prezzi.items():
                # Media dei 7 giorni centrati su questo (3 prima, 3 dopo): contiene ogni giorno
                # della settimana una volta e annulla una salita o discesa costante dei prezzi.
                finestra = [prezzi.get(giorno + timedelta(days=k)) for k in range(-3, 4)]
                if None in finestra:
                    continue  # servono tutti e 7 i giorni attorno
                scarti[giorno.weekday()].append(prezzo - sum(finestra) / 7)
        if not all(scarti):
            continue  # qualche giorno senza dati: per questa categoria non si può dire
        centesimi = [100 * sum(s) / len(s) for s in scarti]
        risultato["categorie"][etichetta] = {
            "centesimi": centesimi,
            "osservazioni": [len(s) for s in scarti],
            "piu_economico": min(range(7), key=centesimi.__getitem__),
            "piu_caro": max(range(7), key=centesimi.__getitem__),
            "scarto_massimo": max(centesimi) - min(centesimi),
        }
    return risultato


def _giorni_mancanti(per_giorno: list[int], ultima: date | None) -> int:
    """Quanti giorni di raccolta servono ancora perché ogni giorno della settimana sia visto
    SETTIMANE_MINIME volte, supponendo di raccogliere un giorno dopo l'altro dopo l'ultimo."""
    if ultima is None:
        return SETTIMANE_MINIME * 7
    conteggi, giorno, mancanti = list(per_giorno), ultima, 0
    while min(conteggi) < SETTIMANE_MINIME:
        giorno += timedelta(days=1)
        conteggi[giorno.weekday()] += 1
        mancanti += 1
    return mancanti
