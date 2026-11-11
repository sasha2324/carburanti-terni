"""Pulizia dei dati: filtro provincia, unione tramite idImpianto, scarti.

Le regole si misurano rispetto alla data di estrazione, mai rispetto a "adesso":
rifacendo la pulizia sugli stessi file si ottiene sempre lo stesso risultato.
Il perché di ogni soglia è spiegato in docs/progetto.md, sezione 2.
"""

import statistics
from collections import defaultdict

from pipeline.leggi import Impianto, Letto, Prezzo

GIORNI_MASSIMI = 7
PREZZO_MINIMO, PREZZO_MASSIMO = 0.30, 5.00  # euro al litro (al kg per il metano)
SCARTO_MASSIMO_DALLA_MEDIANA = 0.25
MINIMO_PER_LA_MEDIANA = 5

# Riquadro attorno alla provincia di Terni, con un po' di margine.
LAT_MIN, LAT_MAX = 42.30, 43.00
LON_MIN, LON_MAX = 11.85, 12.95


class DatiNonPlausibili(Exception):
    """I dati sono leggibili ma non hanno senso: meglio fermarsi che pubblicarli."""


def pulisci(anagrafica: Letto, prezzi: Letto, provincia: str = "TR", minimo_impianti: int = 80) -> dict:
    """Restituisce il contenuto del file del giorno (vedi docs/progetto.md, sezione 3)."""
    if anagrafica.data != prezzi.data:
        raise DatiNonPlausibili(
            f"le date di estrazione dei due file sono diverse: "
            f"anagrafica {anagrafica.data}, prezzi {prezzi.data}"
        )
    estrazione = anagrafica.data

    impianti = {i.id: i for i in anagrafica.righe if i.provincia == provincia}
    if len(impianti) < minimo_impianti:
        raise DatiNonPlausibili(
            f"solo {len(impianti)} impianti in provincia {provincia}, ne servono almeno {minimo_impianti}"
        )

    scartati = []

    def scarta(p: Prezzo, motivo: str):
        scartati.append({**_prezzo_json(p), "id": p.id_impianto, "motivo": motivo})

    # 1. Unione: solo i prezzi degli impianti della provincia. Se un impianto ha due prezzi
    #    per lo stesso carburante e modalità, vale quello comunicato più di recente.
    ultimi: dict[tuple, Prezzo] = {}
    for p in prezzi.righe:
        if p.id_impianto not in impianti:
            continue
        chiave = (p.id_impianto, p.carburante, p.self_service)
        precedente = ultimi.get(chiave)
        if precedente is None:
            ultimi[chiave] = p
        elif p.comunicato > precedente.comunicato:
            scarta(precedente, "duplicato")
            ultimi[chiave] = p
        else:
            scarta(p, "duplicato")

    # 2. Prezzi vecchi e fuori dai limiti assoluti.
    validi = []
    for p in ultimi.values():
        if (estrazione - p.comunicato.date()).days > GIORNI_MASSIMI:
            scarta(p, "vecchio")
        elif not PREZZO_MINIMO <= p.prezzo <= PREZZO_MASSIMO:
            scarta(p, "fuori_scala")
        else:
            validi.append(p)

    # 3. Confronto con la mediana del gruppo (stesso carburante e stessa modalità),
    #    solo per i gruppi abbastanza numerosi da avere una mediana affidabile.
    gruppi = defaultdict(list)
    for p in validi:
        gruppi[(p.carburante, p.self_service)].append(p.prezzo)
    mediane = {
        gruppo: statistics.median(valori)
        for gruppo, valori in gruppi.items()
        if len(valori) >= MINIMO_PER_LA_MEDIANA
    }

    tenuti = defaultdict(list)
    for p in validi:
        mediana = mediane.get((p.carburante, p.self_service))
        if mediana is not None and abs(p.prezzo - mediana) / mediana > SCARTO_MASSIMO_DALLA_MEDIANA:
            scarta(p, "lontano_dalla_mediana")
        else:
            tenuti[p.id_impianto].append(p)

    return {
        "estrazione": estrazione.isoformat(),
        "impianti": [_impianto_json(i, tenuti[i.id]) for i in sorted(impianti.values(), key=lambda i: i.id)],
        "scartati": sorted(scartati, key=lambda s: (s["id"], s["carburante"], not s["self"], s["comunicato"])),
    }


def _impianto_json(impianto: Impianto, prezzi: list[Prezzo]) -> dict:
    lat, lon = _coordinate(impianto)
    return {
        "id": impianto.id,
        "nome": impianto.nome,
        "gestore": impianto.gestore,
        "bandiera": impianto.bandiera,
        "tipo": impianto.tipo,
        "indirizzo": impianto.indirizzo,
        "comune": impianto.comune,
        "lat": lat,
        "lon": lon,
        # prima per carburante, e a parità di carburante prima il self
        "prezzi": [_prezzo_json(p) for p in sorted(prezzi, key=lambda p: (p.carburante, not p.self_service))],
    }


def _prezzo_json(p: Prezzo) -> dict:
    return {
        "carburante": p.carburante,
        "self": p.self_service,
        "prezzo": p.prezzo,
        "comunicato": p.comunicato.isoformat(),
    }


def _coordinate(impianto: Impianto) -> tuple[float | None, float | None]:
    """Le coordinate non sono verificate dal MIMIT: si tengono solo se cadono attorno alla provincia."""
    lat, lon = impianto.lat, impianto.lon
    if lat is None or lon is None:
        return None, None
    if LAT_MIN <= lat <= LAT_MAX and LON_MIN <= lon <= LON_MAX:
        return lat, lon
    return None, None
