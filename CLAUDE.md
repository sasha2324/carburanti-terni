# Carburanti Terni

Sito statico con i prezzi dei carburanti della provincia di Terni (open data MIMIT).
Scelte, formato dei dati e regole di pulizia: `docs/progetto.md`.

## Comandi

- Test: `.venv/bin/python -m pytest`
- Aggiornare i dati (scarica dal MIMIT e salva `data/<estrazione>.json`): `.venv/bin/python -m pipeline`
- Costruire il sito in `dist/`: `.venv/bin/python -m sito.build`

## Regole di lavoro

- Spiegare in breve ogni scelta importante prima di farla: l'utente vuole imparare.
- Piccoli passi, commit chiari in italiano.
- Test per la parte dati (lettura, pulizia, analisi) scritti prima del codice.
- Chiedere prima di installare cose o toccare file fuori da questa cartella.

## Stile

@DESIGN.md

Il DESIGN.md è l'analisi del linguaggio visivo di NerdWallet presa da
[awesome-design-md](https://github.com/VoltAgent/awesome-design-md) (licenza MIT).
Si usa come linguaggio visivo, **non** come marchio: niente nome, logo o slogan di NerdWallet.

Adattamenti al nostro sito:

- Font **Jost** (sostituto indicato dal DESIGN.md per Gotham, che è a pagamento), servito dal sito
  stesso e non da Google Fonts, per non collegare i visitatori a server esterni.
- Non usiamo stelle di valutazione, `marquee-ribbon`, illustrazioni, pulsanti di registrazione.
- La classifica usa `comparison-row` (righe con linea sottile, nessun divisorio verticale) e
  `spec-cell` (etichetta sopra il valore). La fascia verde `hero-band` apre solo l'inizio di ogni pagina.
- Testi in italiano; date nel formato "9 nov, 20:00".
