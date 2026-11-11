"""Grafici SVG generati in Python: nessuna libreria nel browser, si vedono anche senza JavaScript.

I colori non sono scritti qui ma nel CSS (classi "self", "servito", "evidenziata"),
così lo stile resta tutto in un posto. JavaScript aggiunge solo il mirino con i valori.
"""

import json
import math
from datetime import date
from html import escape

from sito.formato import MESI_BREVI, data_giorno_mese, prezzo_testo

LARGHEZZA, ALTEZZA = 400, 220
SINISTRA, DESTRA, ALTO, BASSO = 40, 50, 12, 26
PASSI = [0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5]
DISTANZA_MINIMA_ETICHETTE = 14  # sotto questa distanza le etichette finali si toccherebbero
GIORNI_BUCO = 3  # oltre questo intervallo senza dati la linea si interrompe
GIORNI_PER_ASSE_MENSILE = 45  # oltre questa durata l'asse x mostra i mesi


def grafico_linee(serie: dict[str, list[tuple[str, float]]], titolo: str) -> str | None:
    """Prezzi nel tempo, una linea per serie (es. "self" e "servito"). None se non ci sono dati."""
    serie = {nome: punti for nome, punti in serie.items() if punti}
    if not serie:
        return None

    date_tutte = sorted({d for punti in serie.values() for d, _ in punti})
    inizio = date.fromisoformat(date_tutte[0])
    durata = (date.fromisoformat(date_tutte[-1]) - inizio).days
    valori = [p for punti in serie.values() for _, p in punti]
    tacche = _tacche(min(valori), max(valori))
    y_min, y_max = tacche[0], tacche[-1]
    larghezza_utile = LARGHEZZA - SINISTRA - DESTRA
    altezza_utile = ALTEZZA - ALTO - BASSO

    def x(iso: str) -> float:
        if durata == 0:
            return SINISTRA + larghezza_utile / 2
        return SINISTRA + (date.fromisoformat(iso) - inizio).days / durata * larghezza_utile

    def y(valore: float) -> float:
        return ALTO + (y_max - valore) / (y_max - y_min) * altezza_utile

    parti = []
    for tacca in tacche:  # griglia e valori sull'asse y
        parti.append(f'<line class="griglia" x1="{SINISTRA}" x2="{LARGHEZZA - DESTRA}" y1="{y(tacca):.1f}" y2="{y(tacca):.1f}"/>')
        parti.append(
            f'<text class="asse" x="{SINISTRA - 6}" y="{y(tacca):.1f}" text-anchor="end" dominant-baseline="middle">'
            f"{_etichetta_tacca(tacca, tacche)}</text>"
        )
    if durata > GIORNI_PER_ASSE_MENSILE:  # periodo lungo: sull'asse x l'inizio di ogni mese
        giorno = inizio.replace(day=1)
        while giorno <= date.fromisoformat(date_tutte[-1]):
            if giorno >= inizio:
                parti.append(
                    f'<text class="asse" x="{x(giorno.isoformat()):.1f}" y="{ALTEZZA - 6}" text-anchor="start">'
                    f"{MESI_BREVI[giorno.month - 1]}</text>"
                )
            giorno = date(giorno.year + giorno.month // 12, giorno.month % 12 + 1, 1)
    else:  # periodo breve: prima e ultima data
        for iso in sorted({date_tutte[0], date_tutte[-1]}):
            ancora = "middle" if durata == 0 else ("start" if iso == date_tutte[0] else "end")
            parti.append(f'<text class="asse" x="{x(iso):.1f}" y="{ALTEZZA - 6}" text-anchor="{ancora}">{data_giorno_mese(iso)}</text>')

    finali = []
    for nome, punti in serie.items():
        classe = escape(nome)
        if len(punti) > 1:
            # Dove mancano più di GIORNI_BUCO giorni la linea si interrompe ("M" = riparti da qui).
            comandi, precedente = [], None
            for g, p in punti:
                giorno = date.fromisoformat(g)
                riparti = precedente is None or (giorno - precedente).days > GIORNI_BUCO
                comandi.append(f"{'M' if riparti else 'L'}{x(g):.1f},{y(p):.1f}")
                precedente = giorno
            d = " ".join(comandi)
            parti.append(f'<path class="linea {classe}" d="{d}"/>')
            ultimo = punti[-1]
            parti.append(f'<circle class="punto {classe}" cx="{x(ultimo[0]):.1f}" cy="{y(ultimo[1]):.1f}" r="4"/>')
        else:
            for g, p in punti:
                parti.append(f'<circle class="punto {classe}" cx="{x(g):.1f}" cy="{y(p):.1f}" r="4"/>')
        finali.append((y(punti[-1][1]), x(punti[-1][0]), punti[-1][1]))

    # Il valore finale accanto a ogni linea, solo se le etichette non si sovrappongono.
    altezze = sorted(f[0] for f in finali)
    if all(b - a >= DISTANZA_MINIMA_ETICHETTE for a, b in zip(altezze, altezze[1:])):
        for altezza, posizione, valore in finali:
            parti.append(
                f'<text class="valore" x="{posizione + 8:.1f}" y="{altezza:.1f}" dominant-baseline="middle">'
                f"{prezzo_testo(valore)}</text>"
            )

    # Dati per il mirino (grafico.js): per ogni data, la posizione x e i valori di ogni serie.
    per_data = {iso: {} for iso in date_tutte}
    for nome, punti in serie.items():
        for g, p in punti:
            per_data[g][nome] = prezzo_testo(p)
    mirino = [{"x": round(x(iso), 1), "data": data_giorno_mese(iso), "valori": per_data[iso]} for iso in date_tutte]

    return (
        f'<svg class="grafico" viewBox="0 0 {LARGHEZZA} {ALTEZZA}" role="img" tabindex="0" '
        f'aria-label="{escape(titolo)}: prezzi dal {data_giorno_mese(date_tutte[0])} al {data_giorno_mese(date_tutte[-1])}" '
        f"data-punti='{escape(json.dumps(mirino), quote=True)}' data-alto=\"{ALTO}\" data-basso=\"{ALTEZZA - BASSO}\">"
        + "".join(parti)
        + "</svg>"
    )


def grafico_barre(centesimi: list[float], etichette: list[str], titolo: str) -> str:
    """Barre sopra e sotto lo zero (scarto dalla media dei giorni attorno); evidenziata la più bassa."""
    altezza = 170
    sinistra, destra, alto, basso = 12, 12, 22, 38  # spazio per i valori scritti e per i giorni
    larghezza_utile = LARGHEZZA - sinistra - destra
    # La scala segue i valori veri: sopra lo zero quanto serve al più alto, sotto quanto serve al più basso.
    sopra = max(0.2, max(centesimi))
    sotto = max(0.2, -min(centesimi))
    scala = (altezza - alto - basso) / (sopra + sotto)
    zero = alto + sopra * scala
    banda = larghezza_utile / len(centesimi)
    spessore = min(24, banda * 0.6)
    piu_basso = min(range(len(centesimi)), key=centesimi.__getitem__)
    piu_alto = max(range(len(centesimi)), key=centesimi.__getitem__)

    parti = [f'<line class="zero" x1="{sinistra}" x2="{LARGHEZZA - destra}" y1="{zero:.1f}" y2="{zero:.1f}"/>']
    for i, (valore, etichetta) in enumerate(zip(centesimi, etichette)):
        centro = sinistra + banda * (i + 0.5)
        classe = "barra evidenziata" if i == piu_basso else "barra"
        parti.append(
            f'<path class="{classe}" d="{_barra(centro - spessore / 2, spessore, zero, valore * scala)}">'
            f"<title>{escape(etichetta)}: {_centesimi_testo(valore)}</title></path>"
        )
        parti.append(f'<text class="asse" x="{centro:.1f}" y="{altezza - 6}" text-anchor="middle">{escape(etichetta)}</text>')
        if i in (piu_basso, piu_alto):  # solo gli estremi hanno il numero scritto
            sotto = valore < 0
            y_testo = zero - valore * scala + (14 if sotto else -6)
            parti.append(
                f'<text class="valore" x="{centro:.1f}" y="{y_testo:.1f}" text-anchor="middle">{_centesimi_testo(valore)}</text>'
            )
    return (
        f'<svg class="grafico" viewBox="0 0 {LARGHEZZA} {altezza}" role="img" '
        f'aria-label="{escape(titolo)}: scarto dalla media dei 7 giorni attorno, per giorno della settimana">'
        + "".join(parti)
        + "</svg>"
    )


def _barra(x: float, larghezza: float, zero: float, altezza: float) -> str:
    """Rettangolo con gli angoli arrotondati solo all'estremo del dato, squadrato sullo zero."""
    raggio = min(4, abs(altezza), larghezza / 2)
    if altezza >= 0:  # verso l'alto
        cima = zero - altezza
        return (
            f"M{x:.1f},{zero:.1f} V{cima + raggio:.1f} Q{x:.1f},{cima:.1f} {x + raggio:.1f},{cima:.1f} "
            f"H{x + larghezza - raggio:.1f} Q{x + larghezza:.1f},{cima:.1f} {x + larghezza:.1f},{cima + raggio:.1f} "
            f"V{zero:.1f} Z"
        )
    fondo = zero - altezza
    return (
        f"M{x:.1f},{zero:.1f} V{fondo - raggio:.1f} Q{x:.1f},{fondo:.1f} {x + raggio:.1f},{fondo:.1f} "
        f"H{x + larghezza - raggio:.1f} Q{x + larghezza:.1f},{fondo:.1f} {x + larghezza:.1f},{fondo - raggio:.1f} "
        f"V{zero:.1f} Z"
    )


def _tacche(minimo: float, massimo: float) -> list[float]:
    """Da 2 a 5 valori "tondi" che contengono tutti i prezzi."""
    if massimo - minimo < 0.01:
        minimo, massimo = minimo - 0.01, massimo + 0.01
    for passo in PASSI:
        primo = math.floor(round(minimo / passo, 6)) * passo
        ultimo = math.ceil(round(massimo / passo, 6)) * passo
        quante = round((ultimo - primo) / passo)
        if quante <= 4:
            return [round(primo + i * passo, 3) for i in range(quante + 1)]
    return [round(minimo, 2), round(massimo, 2)]


def _etichetta_tacca(valore: float, tacche: list[float]) -> str:
    decimali = 3 if any(round(t * 100, 6) % 1 for t in tacche) else 2
    return f"{valore:.{decimali}f}".replace(".", ",")


def _centesimi_testo(valore: float) -> str:
    segno = "+" if valore > 0 else ("−" if valore < 0 else "")
    return f"{segno}{abs(valore):.1f}".replace(".", ",") + " cent"
