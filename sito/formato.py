"""Numeri e date in italiano, senza dipendere dalla lingua del computer che costruisce il sito."""

from datetime import date, datetime

MESI = [
    "gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno",
    "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre",
]  # fmt: skip
MESI_BREVI = ["gen", "feb", "mar", "apr", "mag", "giu", "lug", "ago", "set", "ott", "nov", "dic"]
GIORNI = ["lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato", "domenica"]
GIORNI_BREVI = ["lun", "mar", "mer", "gio", "ven", "sab", "dom"]


def prezzo_testo(valore: float) -> str:
    """1.989 -> "1,989" (euro con tre decimali, come li comunica il MIMIT)."""
    return f"{valore:.3f}".replace(".", ",")


def prezzo_parti(valore: float) -> tuple[str, str]:
    """1.989 -> ("1,98", "9"): sui cartelli dei distributori la terza cifra è scritta più piccola."""
    testo = prezzo_testo(valore)
    return testo[:-1], testo[-1]


PREPOSIZIONI = {"di", "del", "della", "dei", "in", "e", "sul", "al"}
ELISIONI = {"d", "dell", "nell", "sull", "l"}


def comune_leggibile(maiuscolo: str) -> str:
    """"CALVI DELL'UMBRIA" -> "Calvi dell'Umbria": maiuscola iniziale, preposizioni minuscole."""
    parole = []
    for i, parola in enumerate(maiuscolo.lower().split()):
        if "'" in parola:
            prima, dopo = parola.split("'", 1)
            prima = prima if (prima in ELISIONI and i > 0) else prima.capitalize()
            parole.append(f"{prima}'{dopo.capitalize()}")
        elif parola in PREPOSIZIONI and i > 0:
            parole.append(parola)
        else:
            parole.append(parola.capitalize())
    return " ".join(parole)


def data_breve(iso: str) -> str:
    """"2026-11-09T20:00:07" -> "9 nov, 20:00"."""
    momento = datetime.fromisoformat(iso)
    return f"{momento.day} {MESI_BREVI[momento.month - 1]}, {momento:%H:%M}"


def data_lunga(iso: str) -> str:
    """"2026-11-10" -> "martedì 10 novembre 2026"."""
    giorno = date.fromisoformat(iso[:10])
    return f"{GIORNI[giorno.weekday()]} {giorno.day} {MESI[giorno.month - 1]} {giorno.year}"


def data_giorno_mese(iso: str) -> str:
    """"2026-11-10" -> "10 nov" (per gli assi dei grafici)."""
    giorno = date.fromisoformat(iso[:10])
    return f"{giorno.day} {MESI_BREVI[giorno.month - 1]}"
