// Schede della classifica (Benzina self, Benzina servito, ...).
// Senza JavaScript si vedono tutte le classifiche una sotto l'altra; con JavaScript una alla volta.
// La scheda scelta finisce nell'indirizzo (#gasolio-self), così il link si può condividere.
(function () {
  const barra = document.querySelector(".schede");
  if (!barra) return;
  const schede = Array.from(barra.querySelectorAll('[role="tab"]'));
  const pannelli = schede.map((s) => document.getElementById(s.getAttribute("aria-controls")));

  function mostra(indice, sceltaUtente) {
    schede.forEach((scheda, i) => {
      const attiva = i === indice;
      scheda.setAttribute("aria-selected", String(attiva));
      scheda.tabIndex = attiva ? 0 : -1;
      pannelli[i].hidden = !attiva;
    });
    // L'indirizzo si aggiorna solo quando sceglie l'utente: se lo si cambia durante il
    // caricamento, il browser scorre la pagina fino al pannello.
    if (sceltaUtente) history.replaceState(null, "", "#" + pannelli[indice].id);
  }

  barra.hidden = false;
  document.documentElement.classList.add("con-schede");
  pannelli.forEach((p, i) => {
    p.setAttribute("role", "tabpanel");
    p.setAttribute("aria-labelledby", schede[i].id);
  });

  schede.forEach((scheda, i) => {
    scheda.addEventListener("click", () => mostra(i, true));
    scheda.addEventListener("keydown", (evento) => {
      const tasti = { ArrowRight: i + 1, ArrowLeft: i - 1, Home: 0, End: schede.length - 1 };
      if (!(evento.key in tasti)) return;
      evento.preventDefault();
      const nuova = (tasti[evento.key] + schede.length) % schede.length;
      mostra(nuova, true);
      schede[nuova].focus();
    });
  });

  const iniziale = pannelli.findIndex((p) => "#" + p.id === location.hash);
  mostra(iniziale >= 0 ? iniziale : 0, false);
})();
