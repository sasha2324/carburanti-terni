// Mirino sui grafici dei prezzi: una linea verticale che segue il puntatore (o le frecce
// della tastiera) e un riquadro con i valori di quel giorno. I dati sono nell'attributo
// data-punti dell'SVG, scritto da sito/grafico.py. Senza JavaScript restano grafico e tabella.
(function () {
  const SVG = "http://www.w3.org/2000/svg";

  document.querySelectorAll("svg.grafico[data-punti]").forEach((svg) => {
    const punti = JSON.parse(svg.dataset.punti);
    const contenitore = svg.parentElement;
    const suggerimento = contenitore.querySelector(".suggerimento");
    const larghezza = svg.viewBox.baseVal.width;

    const mirino = document.createElementNS(SVG, "line");
    mirino.setAttribute("class", "mirino");
    mirino.setAttribute("y1", svg.dataset.alto);
    mirino.setAttribute("y2", svg.dataset.basso);
    mirino.style.display = "none";
    svg.appendChild(mirino);

    let attuale = -1;

    function mostra(indice) {
      attuale = indice;
      const punto = punti[indice];
      mirino.setAttribute("x1", punto.x);
      mirino.setAttribute("x2", punto.x);
      mirino.style.display = "";

      suggerimento.replaceChildren();
      const data = document.createElement("p");
      data.className = "suggerimento-data";
      data.textContent = punto.data;
      suggerimento.appendChild(data);
      for (const [serie, valore] of Object.entries(punto.valori)) {
        const riga = document.createElement("p");
        const chiave = document.createElement("span");
        chiave.className = "chiave " + serie;
        const numero = document.createElement("strong");
        numero.textContent = valore;
        riga.append(chiave, numero, " " + serie);
        suggerimento.appendChild(riga);
      }
      suggerimento.hidden = false;
      const frazione = punto.x / larghezza;
      suggerimento.style.left = frazione * 100 + "%";
      suggerimento.classList.toggle("a-sinistra", frazione > 0.6);
    }

    function nascondi() {
      attuale = -1;
      mirino.style.display = "none";
      suggerimento.hidden = true;
    }

    function piuVicino(clientX) {
      const rettangolo = svg.getBoundingClientRect();
      const x = ((clientX - rettangolo.left) / rettangolo.width) * larghezza;
      let migliore = 0;
      punti.forEach((p, i) => {
        if (Math.abs(p.x - x) < Math.abs(punti[migliore].x - x)) migliore = i;
      });
      return migliore;
    }

    svg.addEventListener("pointermove", (evento) => mostra(piuVicino(evento.clientX)));
    svg.addEventListener("pointerleave", nascondi);
    svg.addEventListener("blur", nascondi);
    svg.addEventListener("focus", () => mostra(punti.length - 1));
    svg.addEventListener("keydown", (evento) => {
      const passo = { ArrowRight: 1, ArrowLeft: -1 }[evento.key];
      if (!passo) return;
      evento.preventDefault();
      mostra(Math.min(punti.length - 1, Math.max(0, (attuale < 0 ? punti.length - 1 : attuale) + passo)));
    });
  });
})();
