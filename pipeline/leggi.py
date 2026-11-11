"""Lettura e controllo del formato dei file MIMIT.

Ogni file è fatto così (metadati MIMIT in vigore dal 10/02/2026):
    Estrazione del AAAA-MM-GG
    <intestazione con i nomi delle colonne>
    <righe di dati con i campi separati da "|">

Se il formato generale non torna si solleva FormatoNonValido e la pipeline si ferma.
Una singola riga rotta invece si salta e si conta, ma se sono troppe ci si ferma lo stesso.
"""

import math
import re
from dataclasses import dataclass
from datetime import date, datetime

SEPARATORE = "|"
INTESTAZIONE_ANAGRAFICA = [
    "idImpianto",
    "Gestore",
    "Bandiera",
    "Tipo Impianto",
    "Nome Impianto",
    "Indirizzo",
    "Comune",
    "Provincia",
    "Latitudine",
    "Longitudine",
]
INTESTAZIONE_PREZZI = ["idImpianto", "descCarburante", "prezzo", "isSelf", "dtComu"]

# Oltre questa quota di righe illeggibili il file è considerato rotto.
MASSIMO_ILLEGGIBILI = 0.01

_PRIMA_RIGA = re.compile(r"Estrazione del (\d{4}-\d{2}-\d{2})")
_INTERO = re.compile(r"[0-9]+")
_DECIMALE = re.compile(r"[0-9]+(\.[0-9]+)?")
_IS_SELF = {"1": True, "0": False}


class FormatoNonValido(Exception):
    """Il file non ha il formato atteso: meglio fermarsi che pubblicare dati rotti."""


@dataclass(frozen=True)
class Impianto:
    id: int
    gestore: str
    bandiera: str
    tipo: str
    nome: str
    indirizzo: str
    comune: str
    provincia: str
    lat: float | None
    lon: float | None


@dataclass(frozen=True)
class Prezzo:
    id_impianto: int
    carburante: str
    prezzo: float
    self_service: bool
    comunicato: datetime


@dataclass(frozen=True)
class Letto:
    """Il contenuto di un file: data di estrazione, righe valide, quante righe sono state saltate."""

    data: date
    righe: list
    illeggibili: int


def leggi_anagrafica(testo: str) -> Letto:
    return _leggi(testo, "anagrafica", INTESTAZIONE_ANAGRAFICA, _impianto)


def leggi_prezzi(testo: str) -> Letto:
    return _leggi(testo, "prezzi", INTESTAZIONE_PREZZI, _prezzo)


def _leggi(testo, nome_file, intestazione, converti_riga):
    righe = testo.removeprefix("﻿").replace("\r\n", "\n").split("\n")

    prima = righe[0].strip()
    trovata = _PRIMA_RIGA.fullmatch(prima)
    try:
        data = date.fromisoformat(trovata.group(1)) if trovata else None
    except ValueError:
        data = None
    if data is None:
        raise FormatoNonValido(
            f"{nome_file}: prima riga inattesa {prima[:80]!r}, attesa 'Estrazione del AAAA-MM-GG'"
        )

    seconda = righe[1].strip() if len(righe) > 1 else ""
    if [campo.strip() for campo in seconda.split(SEPARATORE)] != intestazione:
        raise FormatoNonValido(
            f"{nome_file}: intestazione cambiata (separatore o colonne diversi).\n"
            f"  attesa:  {SEPARATORE.join(intestazione)}\n"
            f"  trovata: {seconda[:200]}"
        )

    dati = [riga for riga in righe[2:] if riga.strip()]
    if not dati:
        raise FormatoNonValido(f"{nome_file}: nessuna riga di dati dopo l'intestazione")

    lette, illeggibili = [], 0
    for riga in dati:
        try:
            lette.append(converti_riga(riga.split(SEPARATORE)))
        except (ValueError, KeyError):
            illeggibili += 1

    if illeggibili > MASSIMO_ILLEGGIBILI * len(dati):
        raise FormatoNonValido(
            f"{nome_file}: {illeggibili} righe illeggibili su {len(dati)} "
            f"(il massimo tollerato è {MASSIMO_ILLEGGIBILI:.0%})"
        )
    return Letto(data=data, righe=lette, illeggibili=illeggibili)


def _impianto(campi: list[str]) -> Impianto:
    if len(campi) < len(INTESTAZIONE_ANAGRAFICA):
        raise ValueError("campi mancanti")
    # Il "|" di troppo, quando c'è, sta nel nome: i primi 4 campi si leggono da sinistra,
    # gli ultimi 4 da destra, e in mezzo l'ultimo pezzo è l'indirizzo.
    centro = campi[4:-4]
    return Impianto(
        id=_intero(campi[0]),
        gestore=_testo(campi[1]),
        bandiera=_testo(campi[2]),
        tipo=_testo(campi[3]),
        nome=_testo(SEPARATORE.join(centro[:-1])),
        indirizzo=_testo(centro[-1]),
        comune=_testo(campi[-4]),
        provincia=_testo(campi[-3]),
        lat=_coordinata(campi[-2]),
        lon=_coordinata(campi[-1]),
    )


def _prezzo(campi: list[str]) -> Prezzo:
    if len(campi) != len(INTESTAZIONE_PREZZI):
        raise ValueError("numero di campi sbagliato")
    valore = campi[2].strip()
    if not _DECIMALE.fullmatch(valore):
        raise ValueError("prezzo non valido")
    return Prezzo(
        id_impianto=_intero(campi[0]),
        carburante=_testo(campi[1]),
        prezzo=float(valore),
        self_service=_IS_SELF[campi[3].strip()],
        comunicato=datetime.strptime(campi[4].strip(), "%d/%m/%Y %H:%M:%S"),
    )


def _testo(campo: str) -> str:
    """Toglie spazi all'inizio e alla fine e riduce spazi doppi e tabulazioni a uno spazio."""
    return " ".join(campo.split())


def _intero(campo: str) -> int:
    campo = campo.strip()
    if not _INTERO.fullmatch(campo):
        raise ValueError("non è un numero intero")
    return int(campo)


def _coordinata(campo: str) -> float | None:
    """Le coordinate sono facoltative: se mancano o non sono numeri diventano None."""
    try:
        valore = float(campo.strip())
    except ValueError:
        return None
    return valore if math.isfinite(valore) else None
