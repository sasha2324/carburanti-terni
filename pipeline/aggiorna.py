"""Pipeline completa: scarica, leggi, pulisci, salva il file del giorno in data/.

Si esegue con `python -m pipeline`. Se qualcosa non va esce con codice 1 e un messaggio
che GitHub Actions mostra in evidenza: in quel caso non viene salvato niente.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from pipeline.leggi import FormatoNonValido, leggi_anagrafica, leggi_prezzi
from pipeline.pulisci import DatiNonPlausibili, pulisci
from pipeline.scarica import URL_ANAGRAFICA, URL_PREZZI, ErroreDownload, scarica

CARTELLA_DATI = Path(__file__).resolve().parent.parent / "data"


class NessunDatoNuovo(Exception):
    """Il file di questa data di estrazione esiste già: il MIMIT non ha ancora pubblicato i dati nuovi."""


def aggiorna(cartella_dati: Path, scarica_testo=scarica, adesso: datetime | None = None) -> Path:
    anagrafica = leggi_anagrafica(scarica_testo(URL_ANAGRAFICA))
    prezzi = leggi_prezzi(scarica_testo(URL_PREZZI))
    pulito = pulisci(anagrafica, prezzi)

    destinazione = cartella_dati / f"{pulito['estrazione']}.json"
    if destinazione.exists():
        raise NessunDatoNuovo(
            f"l'estrazione del {pulito['estrazione']} è già salvata: "
            f"il MIMIT non ha ancora pubblicato i dati nuovi"
        )

    adesso = adesso or datetime.now(timezone.utc)
    contenuto = {"estrazione": pulito["estrazione"], "generato": adesso.isoformat(timespec="seconds"), **pulito}

    # Scrittura "atomica": prima un file temporaneo, poi lo si rinomina.
    # Se il processo si interrompe a metà, in data/ non resta un file troncato.
    cartella_dati.mkdir(parents=True, exist_ok=True)
    temporaneo = destinazione.with_suffix(".json.tmp")
    temporaneo.write_text(json.dumps(contenuto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    os.replace(temporaneo, destinazione)
    return destinazione


def main() -> int:
    try:
        percorso = aggiorna(CARTELLA_DATI)
    except (ErroreDownload, FormatoNonValido, DatiNonPlausibili, NessunDatoNuovo) as errore:
        titolo = type(errore).__name__
        # "::error" è un comando di GitHub Actions; il messaggio va su una riga sola
        print(f"::error title={titolo}::{str(errore).replace(chr(10), ' | ')}", file=sys.stderr)
        print(f"\nERRORE ({titolo}): {errore}", file=sys.stderr)
        return 1

    contenuto = json.loads(percorso.read_text(encoding="utf-8"))
    prezzi = sum(len(i["prezzi"]) for i in contenuto["impianti"])
    print(
        f"Salvato {percorso.name}: {len(contenuto['impianti'])} impianti, "
        f"{prezzi} prezzi, {len(contenuto['scartati'])} prezzi scartati"
    )
    return 0
