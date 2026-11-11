# Prezzi carburanti — provincia di Terni

Sito statico con i prezzi dei carburanti dei distributori della provincia di Terni,
costruito ogni mattina dagli open data del Ministero delle Imprese e del Made in Italy (MIMIT).

- Classifica dei distributori più economici (benzina e gasolio, self e servito)
- Mappa dei distributori
- Pagina di ogni distributore con l'andamento dei prezzi
- Quale giorno della settimana conviene (quando lo storico basta)

Niente server e niente database: una GitHub Action scarica i dati, li pulisce,
salva un file JSON del giorno in `data/` e ricostruisce il sito.

Le scelte di progetto e il formato dei dati sono descritti in [`docs/progetto.md`](docs/progetto.md).

## Lavorare in locale

```sh
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest          # test
.venv/bin/python -m pipeline        # scarica i dati di oggi in data/
.venv/bin/python -m sito.build      # costruisce il sito in dist/
python3 -m http.server -d dist      # anteprima su http://localhost:8000
```

## Pubblicazione

L'Action `.github/workflows/aggiorna.yml` gira ogni giorno alle 9:30 UTC, a mano dal pulsante
"Run workflow" e a ogni push su `main` (in quel caso ricostruisce solo il sito, senza scaricare dati).

Per attivarla la prima volta:

1. Crea un repository **pubblico** su GitHub (GitHub Pages gratuito lo richiede) e carica il progetto.
2. In *Settings → Pages → Build and deployment* scegli **Source: GitHub Actions**.
3. Il primo push pubblica già il sito; dal giorno dopo l'Action aggiunge un file in `data/` ogni mattina.

Se il MIMIT non ha ancora pubblicato i dati nuovi, o il formato dei file cambia, l'Action fallisce
con un messaggio che spiega il motivo, e GitHub te lo segnala per email. In quel caso non viene
salvato né pubblicato niente: il sito resta quello del giorno prima. Si può riprovare con "Run workflow".

## Fonte e licenza dei dati

Dati: [MIMIT — Carburanti, prezzi praticati e anagrafica degli impianti](https://www.mimit.gov.it/it/open-data/elenco-dataset/carburanti-prezzi-praticati-e-anagrafica-degli-impianti),
licenza [IODL 2.0](https://www.dati.gov.it/iodl/2.0/).
