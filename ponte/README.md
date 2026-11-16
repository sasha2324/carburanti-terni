# Il ponte in Europa

Il sito del MIMIT risponde solo alle connessioni dall'Europa: dai server di GitHub Actions,
che sono negli USA, la connessione non si apre (verificato il 16/11/2026: da Italia,
Germania, Paesi Bassi, Regno Unito risponde in 20–200 ms; dagli USA va sempre in timeout).

Il ponte è una funzione **AWS Lambda a Francoforte** (`lambda_function.py`, un file solo,
solo libreria standard). Ogni mattina l'Action le chiede i due file; lei li scarica
dall'Europa e li restituisce compressi. Tutto il resto (pulizia, file del giorno, sito)
resta nell'Action.

```
GitHub Actions (USA) ──?file=prezzi + chiave──> Lambda (Francoforte) ──> MIMIT
                     <──── file compresso ─────
```

- Risponde solo con l'intestazione `X-Chiave-Ponte` giusta (variabile `CHIAVE_PONTE`).
- Scarica solo i due file del MIMIT: non è un proxy aperto.
- Su GitHub servono due secret: `MIMIT_PONTE_URL` (l'indirizzo della funzione) e
  `MIMIT_PONTE_CHIAVE` (la stessa chiave). Senza, la pipeline scarica direttamente dal
  MIMIT: è quello che succede sul Mac.

## Installare o aggiornare

Da **AWS CloudShell** (icona del terminale in alto nella console AWS), con la regione
**Europa (Francoforte)** selezionata in alto a destra:

```sh
git clone https://github.com/sasha2324/carburanti-terni
CHIAVE_PONTE='la-chiave' bash carburanti-terni/ponte/installa.sh
```

Lo script crea il ruolo, la funzione e l'indirizzo pubblico, poi prova a scaricare il file
dei prezzi e stampa l'indirizzo da mettere in `MIMIT_PONTE_URL`. Si può rilanciare: per
aggiornare il codice basta `git pull` nella cartella e lo stesso comando.

## Costi

Una chiamata al giorno rientra largamente nel piano gratuito di Lambda. Per sicurezza
conviene creare in AWS un budget con avviso a 1 dollaro (Billing → Budgets).

## Cambiare la chiave

1. Nuova chiave su GitHub: `gh secret set MIMIT_PONTE_CHIAVE -R sasha2324/carburanti-terni`
2. Stessa chiave sulla funzione: rilanciare `installa.sh` con `CHIAVE_PONTE='nuova'`.
