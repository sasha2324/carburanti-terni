"""Importa lo storico dall'archivio trimestrale del MIMIT.

L'archivio (https://www.mimit.gov.it/it/open-data/elenco-dataset/carburanti-archivio-prezzi) ha un
.tar.gz per trimestre con un CSV dei prezzi per giorno: prezzo_alle_8-AAAAMMGG.csv. Ogni giorno passa
dalla stessa lettura e pulizia della pipeline giornaliera e diventa un file di data/.

L'archivio dei prezzi non dice in che comune è un impianto: si usa l'anagrafica attuale, e lo si
scrive nel campo "fonte". Gli impianti chiusi nel frattempo quindi non compaiono.
Attenzione: fino al 9/02/2026 i file usavano il separatore ";", che il lettore non accetta.

Uso:
    python -m pipeline.archivio 2026_3_tr.tar.gz [altro.tar.gz ...] [--anagrafica anagrafica.csv]
Senza --anagrafica si scarica quella attuale dal MIMIT.
"""

import argparse
import re
import sys
import tarfile
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path

from pipeline.aggiorna import CARTELLA_DATI, salva_giorno
from pipeline.leggi import FormatoNonValido, Letto, leggi_anagrafica, leggi_prezzi
from pipeline.pulisci import DatiNonPlausibili, pulisci
from pipeline.scarica import URL_ANAGRAFICA, scarica

_FILE_DEI_PREZZI = re.compile(r"prezzo_alle_8-\d{8}\.csv$")


@dataclass
class Esito:
    salvati: list[str] = field(default_factory=list)
    gia_presenti: list[str] = field(default_factory=list)
    saltati: list[tuple[str, str]] = field(default_factory=list)  # (nome del file, motivo)


def importa(archivi: list[Path], anagrafica: Letto, cartella_dati: Path, adesso: datetime | None = None) -> Esito:
    adesso = adesso or datetime.now(timezone.utc)
    esito = Esito()
    for archivio in archivi:
        for nome, contenuto in _giorni(archivio):
            try:
                prezzi = leggi_prezzi(contenuto.decode("utf-8"))
                # L'anagrafica è di oggi: le si dà la data del giorno dell'archivio per poterle unire.
                pulito = pulisci(replace(anagrafica, data=prezzi.data), prezzi)
            except (UnicodeDecodeError, FormatoNonValido, DatiNonPlausibili) as errore:
                esito.saltati.append((nome, str(errore)))
                continue

            destinazione = cartella_dati / f"{pulito['estrazione']}.json"
            if destinazione.exists():
                esito.gia_presenti.append(pulito["estrazione"])
                continue
            salva_giorno(
                destinazione,
                {
                    "estrazione": pulito["estrazione"],
                    "generato": adesso.isoformat(timespec="seconds"),
                    "fonte": f"archivio MIMIT, anagrafica del {anagrafica.data.isoformat()}",
                    **pulito,
                },
            )
            esito.salvati.append(pulito["estrazione"])
    esito.salvati.sort()
    esito.gia_presenti.sort()
    return esito


def _giorni(archivio: Path):
    """I file dei prezzi dentro l'archivio, letti in memoria: niente viene estratto su disco."""
    with tarfile.open(archivio, "r:gz") as tar:
        for voce in tar:
            if voce.isfile() and _FILE_DEI_PREZZI.search(voce.name):
                yield Path(voce.name).name, tar.extractfile(voce).read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Importa lo storico dall'archivio trimestrale del MIMIT.")
    parser.add_argument("archivi", nargs="+", type=Path, help="file .tar.gz dei prezzi (es. 2026_3_tr.tar.gz)")
    parser.add_argument("--anagrafica", type=Path, help="CSV dell'anagrafica da usare (predefinito: quella attuale)")
    argomenti = parser.parse_args()

    testo = argomenti.anagrafica.read_text(encoding="utf-8") if argomenti.anagrafica else scarica(URL_ANAGRAFICA)
    esito = importa(argomenti.archivi, leggi_anagrafica(testo), CARTELLA_DATI)

    if esito.salvati:
        print(f"Salvati {len(esito.salvati)} giorni, dal {esito.salvati[0]} al {esito.salvati[-1]}")
    if esito.gia_presenti:
        print(f"Già presenti (non toccati): {len(esito.gia_presenti)} giorni")
    for nome, motivo in esito.saltati:
        print(f"::warning title=Giorno saltato::{nome}: {motivo.replace(chr(10), ' | ')}", file=sys.stderr)
    return 1 if esito.saltati and not esito.salvati else 0


if __name__ == "__main__":
    sys.exit(main())
