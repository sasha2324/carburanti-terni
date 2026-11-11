"""Costruisce il sito statico in dist/ a partire dai file di data/.

Si esegue con: python -m sito.build
"""

import json
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from sito.analisi import CATEGORIE, classifica, giorno_della_settimana, storico
from sito.formato import (
    GIORNI,
    GIORNI_BREVI,
    comune_leggibile,
    data_breve,
    data_giorno_mese,
    data_lunga,
    prezzo_parti,
    prezzo_testo,
)
from sito.grafico import grafico_barre, grafico_linee

CARTELLA = Path(__file__).resolve().parent
PROGETTO = CARTELLA.parent

FONTE = {
    "url": "https://www.mimit.gov.it/it/open-data/elenco-dataset/carburanti-prezzi-praticati-e-anagrafica-degli-impianti",
    "licenza_url": "https://www.dati.gov.it/iodl/2.0/",
}
MOSTRATI_SUBITO = 10  # righe visibili di ogni classifica; le altre dietro "Mostra tutti"


def carica_giorni(cartella_dati: Path) -> list[dict]:
    file = sorted(cartella_dati.glob("*.json"))
    if not file:
        raise FileNotFoundError(f"nessun file di dati in {cartella_dati}")
    giorni = [json.loads(f.read_text(encoding="utf-8")) for f in file]
    return sorted(giorni, key=lambda g: g["estrazione"])


def costruisci(cartella_dati: Path, uscita: Path) -> None:
    giorni = carica_giorni(cartella_dati)
    oggi = giorni[-1]
    serie = storico(giorni)

    ambiente = Environment(
        loader=FileSystemLoader(CARTELLA / "templates"),
        autoescape=True,  # i testi dei dati vengono protetti: un "<" resta un "<" e non diventa HTML
        undefined=StrictUndefined,  # una variabile scritta male nel template è un errore, non un vuoto
        trim_blocks=True,
        lstrip_blocks=True,
    )
    ambiente.filters.update(
        prezzo=prezzo_testo,
        prezzo_parti=prezzo_parti,
        data_breve=data_breve,
        data_lunga=data_lunga,
        data_giorno_mese=data_giorno_mese,
        comune=comune_leggibile,
        nome=nome_impianto,
    )
    comune = {
        "oggi": oggi,
        "fonte": FONTE,
        "primo_giorno": giorni[0]["estrazione"],
        "giorni_raccolti": len(giorni),
    }

    if uscita.exists():
        shutil.rmtree(uscita)
    shutil.copytree(CARTELLA / "static", uscita / "static")

    def scrivi(percorso: str, template: str, **contesto):
        destinazione = uscita / percorso
        destinazione.parent.mkdir(parents=True, exist_ok=True)
        radice = "../" * percorso.count("/")
        html = ambiente.get_template(template).render(**comune, **contesto, radice=radice)
        destinazione.write_text(html, encoding="utf-8")

    classifiche = [
        {
            "etichetta": etichetta,
            "id": etichetta.lower().replace(" ", "-"),
            "righe": classifica(oggi, carburante, self_service),
        }
        for carburante, self_service, etichetta in CATEGORIE
    ]
    cartelli = [c for c in classifiche if c["etichetta"] in ("Benzina self", "Gasolio self") and c["righe"]]
    scrivi("index.html", "index.html", pagina="classifica", classifiche=classifiche, cartelli=cartelli, mostrati=MOSTRATI_SUBITO)

    scrivi("mappa.html", "mappa.html", pagina="mappa", punti=punti_mappa(oggi), categorie=[c[2] for c in CATEGORIE])

    analisi = giorno_della_settimana(giorni)
    for etichetta, risultato in analisi["categorie"].items():
        risultato["svg"] = grafico_barre(risultato["centesimi"], GIORNI_BREVI, titolo=etichetta)
    scrivi("giorno-della-settimana.html", "giorno.html", pagina="giorno", analisi=analisi, nomi_giorni=GIORNI)

    for impianto in oggi["impianti"]:
        grafici = []
        for carburante in ("Benzina", "Gasolio"):
            per_impianto = serie.get(impianto["id"], {})
            dati = {"self": per_impianto.get((carburante, True), []), "servito": per_impianto.get((carburante, False), [])}
            svg = grafico_linee(dati, titolo=carburante)
            if svg:
                grafici.append({"carburante": carburante, "svg": svg, "tabella": tabella_storico(dati)})
        scrivi(f"distributore/{impianto['id']}.html", "distributore.html", pagina="distributore", impianto=impianto, grafici=grafici)


def nome_impianto(impianto: dict) -> str:
    """Alcuni impianti non hanno un nome: si usa la bandiera."""
    return impianto["nome"] or impianto.get("bandiera") or f"Impianto {impianto['id']}"


def punti_mappa(giorno: dict) -> list[dict]:
    """I dati che servono alla mappa, solo per gli impianti con coordinate."""
    punti = []
    for impianto in giorno["impianti"]:
        if impianto["lat"] is None:
            continue
        prezzi = {}
        for carburante, self_service, etichetta in CATEGORIE:
            for p in impianto["prezzi"]:
                if p["carburante"] == carburante and p["self"] == self_service:
                    prezzi[etichetta] = p["prezzo"]
        punti.append(
            {
                "id": impianto["id"],
                "nome": nome_impianto(impianto),
                "comune": comune_leggibile(impianto["comune"]),
                "indirizzo": impianto["indirizzo"],
                "lat": impianto["lat"],
                "lon": impianto["lon"],
                "prezzi": prezzi,
            }
        )
    return punti


def tabella_storico(dati: dict[str, list[tuple[str, float]]]) -> list[dict]:
    """La versione in tabella del grafico: una riga per data, dalla più recente."""
    per_data: dict[str, dict] = {}
    for nome, punti in dati.items():
        for data, prezzo in punti:
            per_data.setdefault(data, {})[nome] = prezzo
    return [{"data": data, **valori} for data, valori in sorted(per_data.items(), reverse=True)]


def main() -> int:
    costruisci(PROGETTO / "data", PROGETTO / "dist")
    pagine = len(list((PROGETTO / "dist").rglob("*.html")))
    print(f"Sito costruito in dist/: {pagine} pagine")
    return 0


if __name__ == "__main__":
    sys.exit(main())
