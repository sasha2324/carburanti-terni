# Prezzi carburanti a Terni

**Cosa fa:** mostra i prezzi dei carburanti dei distributori del comune di Terni, presi
dagli open data del Ministero delle Imprese e del Made in Italy (MIMIT):
classifica dei più economici (benzina e gasolio, self e servito), mappa, andamento dei prezzi
di ogni distributore e quale giorno della settimana conviene.

**Con cosa è fatto:** Python (scarica e pulisce i dati, genera le pagine con Jinja2), Leaflet
e OpenStreetMap per la mappa, test con pytest. Niente server né database: una GitHub Action
salva un file JSON del giorno in `data/` e pubblica il sito su GitHub Pages.

**Stato:** online: <https://sasha2324.github.io/carburanti-terni/>. L'aggiornamento automatico
è in pausa (vedi sotto): per ora i dati si aggiornano a mano dal Mac.
Scelte di progetto e formato dei dati in [`docs/progetto.md`](docs/progetto.md).

## Avviarlo

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest          # test
.venv/bin/python -m pipeline        # scarica i dati di oggi in data/
(cd scene-3d && npm install && npm run build)   # la scena 3D di «Come funziona» (Node.js 24)
.venv/bin/python -m sito.build      # costruisce il sito in dist/
python3 -m http.server -d dist      # anteprima su http://localhost:8000
```

## Aggiornamento automatico

L'Action `.github/workflows/aggiorna.yml` gira a mano con "Run workflow" e a ogni push su
`main` (in quel caso ricostruisce solo il sito).

**In pausa dal 16/11/2026.** Il MIMIT risponde solo dall'Europa, mentre GitHub è negli USA:
da lì il download va sempre in timeout. La soluzione pronta è un piccolo «ponte» su AWS a
Francoforte ([`ponte/`](ponte/README.md)), non ancora installato. Nel frattempo l'orario
giornaliero è spento e i dati si aggiornano dal Mac:

```sh
.venv/bin/python -m pipeline   # salva data/<giorno>.json
git add data/ && git commit -m "Dati: estrazione del <giorno>" && git push   # l'Action pubblica
```

Per riaccendere l'aggiornamento automatico: installare il ponte, mettere il secret
`MIMIT_PONTE_URL` e togliere il commento da `schedule` nel workflow.
Se il MIMIT non ha ancora pubblicato i dati o il formato cambia, l'Action fallisce con un
messaggio che spiega il motivo e non pubblica niente: resta online il sito del giorno prima.

## Storico dall'archivio del MIMIT

I mesi passati vengono dall'[archivio trimestrale](https://www.mimit.gov.it/it/open-data/elenco-dataset/carburanti-archivio-prezzi).
Quando esce un trimestre nuovo (il quarto del 2026 dovrebbe arrivare a inizio gennaio 2027):

```sh
curl -LO https://opendatacarburanti.mise.gov.it/categorized/prezzo_alle_8/2026/2026_4_tr.tar.gz
.venv/bin/python -m pipeline.archivio 2026_4_tr.tar.gz   # i giorni già presenti non vengono toccati
```

Il `.tar.gz` (circa 50 MB) non va nel repository: servono solo i file del giorno in `data/`.

## Fonte e licenza dei dati

Dati: [MIMIT — Carburanti, prezzi praticati e anagrafica degli impianti](https://www.mimit.gov.it/it/open-data/elenco-dataset/carburanti-prezzi-praticati-e-anagrafica-degli-impianti),
licenza [IODL 2.0](https://www.dati.gov.it/iodl/2.0/).
