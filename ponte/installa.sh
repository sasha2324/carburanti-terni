#!/usr/bin/env bash
# Installa (o aggiorna) il ponte su AWS Lambda, regione Francoforte.
# Si lancia da AWS CloudShell (il terminale dentro la console AWS), così non serve
# installare niente sul Mac né creare chiavi d'accesso:
#
#   git clone https://github.com/sasha2324/carburanti-terni
#   CHIAVE_PONTE='la-chiave' bash carburanti-terni/ponte/installa.sh
#
# La chiave deve essere la stessa del secret MIMIT_PONTE_CHIAVE su GitHub.
# Rilanciarlo è sicuro: se qualcosa esiste già, lo aggiorna invece di ricrearlo.
set -euo pipefail

export AWS_DEFAULT_REGION=eu-central-1 # Francoforte: dalla Germania il MIMIT risponde
NOME=ponte-mimit
RUOLO=ponte-mimit-ruolo
CHIAVE="${CHIAVE_PONTE:?manca la variabile CHIAVE_PONTE (vedi le istruzioni in cima a questo file)}"
CARTELLA="$(cd "$(dirname "$0")" && pwd)"
ZIP=/tmp/ponte-mimit.zip

echo "1/5 Preparo il codice"
rm -f "$ZIP"
(cd "$CARTELLA" && zip -q "$ZIP" lambda_function.py)

echo "2/5 Ruolo della funzione (può solo scrivere i propri log)"
if ! aws iam get-role --role-name "$RUOLO" >/dev/null 2>&1; then
  aws iam create-role --role-name "$RUOLO" --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}]
  }' >/dev/null
  aws iam attach-role-policy --role-name "$RUOLO" \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  echo "    ruolo creato, aspetto che diventi utilizzabile..."
  sleep 15
fi
ARN_RUOLO=$(aws iam get-role --role-name "$RUOLO" --query Role.Arn --output text)

echo "3/5 Funzione $NOME"
if aws lambda get-function --function-name "$NOME" >/dev/null 2>&1; then
  aws lambda update-function-code --function-name "$NOME" --zip-file "fileb://$ZIP" >/dev/null
  aws lambda wait function-updated-v2 --function-name "$NOME"
  aws lambda update-function-configuration --function-name "$NOME" \
    --runtime python3.14 --timeout 60 --memory-size 256 \
    --environment "Variables={CHIAVE_PONTE=$CHIAVE}" >/dev/null
  aws lambda wait function-updated-v2 --function-name "$NOME"
else
  aws lambda create-function --function-name "$NOME" \
    --runtime python3.14 --architectures arm64 \
    --handler lambda_function.lambda_handler --role "$ARN_RUOLO" \
    --zip-file "fileb://$ZIP" --timeout 60 --memory-size 256 \
    --environment "Variables={CHIAVE_PONTE=$CHIAVE}" >/dev/null
  aws lambda wait function-active-v2 --function-name "$NOME"
fi

echo "4/5 Indirizzo pubblico (protetto dalla chiave, controllata nel codice)"
if ! aws lambda get-function-url-config --function-name "$NOME" >/dev/null 2>&1; then
  aws lambda create-function-url-config --function-name "$NOME" --auth-type NONE >/dev/null
  # Da ottobre 2025 servono due permessi: uno per l'URL, uno per l'esecuzione tramite URL
  aws lambda add-permission --function-name "$NOME" --statement-id UrlPubblico \
    --action lambda:InvokeFunctionUrl --principal '*' --function-url-auth-type NONE >/dev/null
  aws lambda add-permission --function-name "$NOME" --statement-id UrlPubblicoInvoke \
    --action lambda:InvokeFunction --principal '*' --invoked-via-function-url >/dev/null
  sleep 5
fi
URL=$(aws lambda get-function-url-config --function-name "$NOME" --query FunctionUrl --output text)

echo "5/5 Prova: chiedo al ponte il file dei prezzi"
codice=$(curl -sS -o /tmp/prezzi.gz -w '%{http_code}' -H "X-Chiave-Ponte: $CHIAVE" "${URL}?file=prezzi" || true)
if [ "$codice" = "200" ]; then
  echo "    OK: $(gzip -dc /tmp/prezzi.gz | head -n 1) ($(stat -c %s /tmp/prezzi.gz) byte compressi)"
else
  echo "    ATTENZIONE: il ponte ha risposto $codice"
  cat /tmp/prezzi.gz 2>/dev/null; echo
  exit 1
fi

echo
echo "Fatto. Indirizzo del ponte (va nel secret MIMIT_PONTE_URL su GitHub):"
echo "$URL"
