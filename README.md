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

## Fonte e licenza dei dati

Dati: [MIMIT — Carburanti, prezzi praticati e anagrafica degli impianti](https://www.mimit.gov.it/it/open-data/elenco-dataset/carburanti-prezzi-praticati-e-anagrafica-degli-impianti),
licenza [IODL 2.0](https://www.dati.gov.it/iodl/2.0/).
