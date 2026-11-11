# Progetto: prezzi carburanti a Terni

Questo file raccoglie le scelte fatte e il perché. Se una scelta cambia, si aggiorna qui.

## 1. I dati di partenza

Fonte: [MIMIT — Carburanti, prezzi praticati e anagrafica degli impianti](https://www.mimit.gov.it/it/open-data/elenco-dataset/carburanti-prezzi-praticati-e-anagrafica-degli-impianti).
Licenza IODL 2.0. Documento di riferimento: `Metadati_prezzi_carburanti_20260128.pdf`
(versione in vigore dal 10 febbraio 2026).

| File | URL |
|---|---|
| Anagrafica | `https://www.mimit.gov.it/images/exportCSV/anagrafica_impianti_attivi.csv` |
| Prezzi | `https://www.mimit.gov.it/images/exportCSV/prezzo_alle_8.csv` |

Formato comune ai due file (dal PDF, verificato sui file veri dell'11/11/2026):

- prima riga: `Estrazione del AAAA-MM-GG`; seconda riga: intestazione; poi i dati
- separatore di colonna `|` (dal 10/02/2026); decimali con il punto
- codifica UTF-8
- i prezzi sono quelli **in vigore alle 8 del giorno di estrazione**: il file pubblicato
  l'11 novembre dice `Estrazione del 2026-11-10`

Anagrafica (`idImpianto|Gestore|Bandiera|Tipo Impianto|Nome Impianto|Indirizzo|Comune|Provincia|Latitudine|Longitudine`):

- `Tipo Impianto`: `Stradale` o `Autostradale`
- `Provincia`: il PDF dice "nome della provincia", il file contiene la **sigla** (`TR`). Ci basiamo sul file
- coordinate in gradi decimali, "inserite su base volontaria e non sempre verificate"

Prezzi (`idImpianto|descCarburante|prezzo|isSelf|dtComu`):

- `descCarburante`: `Benzina`, `Gasolio`, `GPL`, `Metano` più i prodotti speciali (Blue Diesel, HVO, …)
- `prezzo`: euro con 3 decimali, al litro (al kg per il metano)
- `isSelf`: `1` self-service, `0` servito
- `dtComu`: `GG/MM/AAAA hh:mm:ss`, il momento in cui il gestore ha comunicato il prezzo

Sporcizia vista nei file veri:

- 110 righe dell'anagrafica nazionale hanno un `|` dentro il nome (11–12 campi invece di 10).
  Oggi nessuna è di Terni, ma il parser le deve gestire
- prezzi assurdi a livello nazionale (0,10 €, 8,888 €)
- un carattere di tabulazione dentro un nome

Fotografia al 10/11/2026: in provincia 132 impianti in 30 comuni; nel **comune di Terni** 48 impianti
(42 con almeno un prezzo recente) e 167 prezzi, nessuno più vecchio di 7 giorni.

## 2. Pulizia

Ogni regola si applica rispetto alla **data di estrazione**, non alla data di oggi: rifacendo la pulizia
sugli stessi file si ottiene sempre lo stesso risultato.

1. **Unione** dei due file tramite `idImpianto`; si tengono solo gli impianti con `Comune == "TERNI"` e
   `Provincia == "TR"`. Il comune comprende anche le frazioni (Piediluco, Marmore, Collestatte…).
   Fino all'11/11/2026 si teneva tutta la provincia: la scelta è cambiata perché interessa solo la città.
2. **Righe con troppi campi** nell'anagrafica: i primi 4 campi si leggono da sinistra e gli ultimi 4
   (comune, provincia, lat, lon) da destra; in mezzo l'ultimo pezzo è l'indirizzo e il resto,
   riunito con `|`, è il nome (nei casi veri il `|` di troppo sta nel nome, es. `STOIL SIMPLE | gestori…`).
   Una riga con **meno** campi del previsto non è recuperabile e si salta.
3. **Prezzi vecchi**: si scarta un prezzo comunicato più di 7 giorni prima della data di estrazione.
4. **Fuori scala, livello 1 (assoluto)**: si scarta un prezzo fuori da 0,30–5,00 €. Il limite è largo
   perché il GPL vero costa ~0,55 €/l e il metano arriva vicino a 5 €/kg: serve solo per gli errori
   grossolani.
5. **Fuori scala, livello 2 (relativo)**: per ogni gruppo (carburante, self/servito) con almeno 5 prezzi
   nel comune si calcola la mediana; si scarta un prezzo che se ne allontana di più del 25%.
   Serve per gli errori di battitura (1,199 al posto di 2,199). Al 10/11/2026 lo scarto massimo
   di un prezzo vero è +16%.
6. **Coordinate**: se sono vuote, zero o fuori da un riquadro attorno al comune
   (lat 42,45–42,68, lon 12,45–12,85) diventano `null`. L'impianto resta in classifica ma non va sulla mappa.
7. **Duplicati** (stesso impianto, carburante e modalità): si tiene il prezzo comunicato più di recente.

Tutto ciò che viene scartato finisce nel JSON con il motivo, così si può controllare.

## 3. Il file del giorno

`data/AAAA-MM-GG.json`, con la data di estrazione nel nome. Contiene solo il comune di Terni, già pulito,
con **tutti** i carburanti (la classifica usa solo Benzina e Gasolio, ma un dato non salvato oggi è perso).

```json
{
  "estrazione": "2026-11-10",
  "generato": "2026-11-11T07:05:12+00:00",
  "impianti": [
    {
      "id": 12345,
      "nome": "…", "gestore": "…", "bandiera": "…", "tipo": "Stradale",
      "indirizzo": "…", "comune": "TERNI",
      "lat": 42.56, "lon": 12.64,
      "prezzi": [
        {"carburante": "Benzina", "self": true, "prezzo": 1.989, "comunicato": "2026-11-09T20:00:07"}
      ]
    }
  ],
  "scartati": [
    {"id": 12345, "carburante": "Gasolio", "self": false, "prezzo": 2.4, "motivo": "vecchio"}
  ]
}
```

`comunicato` è l'ora italiana così come la scrive il MIMIT. Il file è indentato per essere leggibile:
circa 35 KB al giorno, che git comprime molto bene perché da un giorno all'altro cambia poco.

## 4. Quando l'aggiornamento si ferma

La pipeline si ferma con un messaggio chiaro e **non salva niente** se:

- il download fallisce (errore di rete, codice HTTP diverso da 200, file vuoto)
- la prima riga non è `Estrazione del AAAA-MM-GG`, o i due file hanno date diverse
- l'intestazione non è esattamente quella attesa (per esempio è cambiato il separatore)
- più dell'1% delle righe di un file non è leggibile (campi mancanti, prezzo o data non validi)
- nel comune di Terni risultano meno di 30 impianti (l'11/11/2026 erano 48)
- il file di quella data di estrazione esiste già (il MIMIT non ha ancora pubblicato i dati nuovi)

Nella GitHub Action il commit e la pubblicazione sono gli ultimi passi: se un passo prima fallisce,
non vengono eseguiti.

Orario: l'11/11/2026 il MIMIT ha pubblicato i file alle 07:45–07:51 UTC (intestazione `Last-Modified`).
L'Action parte più tardi per avere margine e si può anche avviare a mano.

## 5. Il sito

Statico, generato da Python con Jinja2 in `dist/`, pubblicato su GitHub Pages.

- **Classifica**: i più economici per Benzina self, Benzina servito, Gasolio self, Gasolio servito,
  ognuno con la data di comunicazione del prezzo
- **Mappa**: Leaflet + mappe OpenStreetMap
- **Distributore**: una pagina per impianto con il grafico dei prezzi nel tempo (SVG generato da Python,
  nessuna libreria di grafici)
- **Giorno della settimana**: l'analisi compare con almeno 8 settimane di storico; prima la pagina dice
  quanti giorni mancano. Metodo: per ogni distributore e settimana si confronta il prezzo di ogni giorno
  con la media di quella settimana, poi si fa la media per giorno della settimana
- **Footer di ogni pagina**: fonte MIMIT, licenza IODL 2.0, attribuzione OpenStreetMap dove serve

## 6. Struttura

```
.github/workflows/aggiorna.yml   automazione giornaliera
pipeline/                        scarica, leggi (formato), pulisci, aggiorna (esegue tutto: python -m pipeline)
sito/                            build.py, templates/, static/
data/                            un JSON per giorno di estrazione
tests/                           pytest + CSV finti in tests/fixtures/
docs/progetto.md                 questo file
```

## 7. Passi

1. Repository, README, questo documento
2. Ambiente Python e dipendenze (`jinja2`, `pytest`)
3. Lettura e controllo del formato, con test
4. Pulizia, con test
5. Download e pipeline completa; primo JSON vero in `data/`
6. Sito: stile, classifica, mappa, distributore, giorno della settimana
7. GitHub Action e pubblicazione su GitHub Pages
