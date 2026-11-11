// Mappa dei distributori con Leaflet e le mappe di OpenStreetMap.
// I dati arrivano dal blocco <script id="dati-mappa"> scritto da sito/build.py.
// I testi dei dati si inseriscono sempre con textContent, mai come HTML.
(function () {
  const contenitore = document.getElementById("mappa");
  if (!contenitore || typeof L === "undefined") return;

  const punti = JSON.parse(document.getElementById("dati-mappa").textContent);
  const PIU_ECONOMICI = 10;
  const colori = getComputedStyle(document.documentElement);
  const verde = colori.getPropertyValue("--primary").trim();
  const grigio = colori.getPropertyValue("--faint").trim();

  const mappa = L.map(contenitore, { scrollWheelZoom: false });
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(mappa);
  mappa.fitBounds(L.latLngBounds(punti.map((p) => [p.lat, p.lon])), { padding: [24, 24] });

  const strato = L.layerGroup().addTo(mappa);

  function prezzoTesto(valore) {
    return valore.toFixed(3).replace(".", ",") + " €/l";
  }

  function scheda(punto, categoria) {
    const radice = document.createElement("div");
    radice.className = "scheda-mappa";
    const nome = document.createElement("a");
    nome.href = "distributore/" + punto.id + ".html";
    nome.textContent = punto.nome;
    const dove = document.createElement("p");
    dove.textContent = punto.indirizzo + ", " + punto.comune;
    const prezzo = document.createElement("p");
    const valore = punto.prezzi[categoria];
    if (valore === undefined) {
      prezzo.textContent = "Nessun prezzo recente per " + categoria.toLowerCase();
    } else {
      const forte = document.createElement("strong");
      forte.textContent = prezzoTesto(valore);
      prezzo.append(categoria + ": ", forte);
    }
    radice.append(nome, dove, prezzo);
    return radice;
  }

  function disegna(categoria) {
    strato.clearLayers();
    const conPrezzo = punti.filter((p) => p.prezzi[categoria] !== undefined);
    const migliori = new Set(
      conPrezzo
        .slice()
        .sort((a, b) => a.prezzi[categoria] - b.prezzi[categoria])
        .slice(0, PIU_ECONOMICI)
        .map((p) => p.id)
    );
    // Prima i punti grigi, poi i verdi: così i più economici stanno sopra.
    const ordinati = punti.slice().sort((a, b) => migliori.has(a.id) - migliori.has(b.id));
    for (const punto of ordinati) {
      const haPrezzo = punto.prezzi[categoria] !== undefined;
      const economico = migliori.has(punto.id);
      const stile = economico
        ? { radius: 9, color: "#ffffff", weight: 2, fillColor: verde, fillOpacity: 1 }
        : haPrezzo
          ? { radius: 6, color: "#ffffff", weight: 2, fillColor: grigio, fillOpacity: 1 }
          : { radius: 5, color: grigio, weight: 2, fillColor: "#ffffff", fillOpacity: 1 };
      const etichetta = document.createElement("span");
      etichetta.textContent = punto.nome + (haPrezzo ? ", " + prezzoTesto(punto.prezzi[categoria]) : "");
      L.circleMarker([punto.lat, punto.lon], stile)
        .bindPopup(() => scheda(punto, categoria))
        .bindTooltip(etichetta)
        .addTo(strato);
    }
  }

  const scelte = document.querySelectorAll('input[name="categoria"]');
  scelte.forEach((scelta) => scelta.addEventListener("change", () => disegna(scelta.value)));
  disegna(document.querySelector('input[name="categoria"]:checked').value);
})();
