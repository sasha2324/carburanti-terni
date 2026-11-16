// "Come funziona" page: the path of the data, step by step.
// Without JavaScript the five steps are a simple list with all the texts.
// With JavaScript: one step at a time, packets moving in a loop and a Pause button.
// On phones the panel opens right under the chosen step.
(function () {
  const root = document.querySelector("[data-percorso]");
  if (!root) return;

  const steps = Array.from(root.querySelectorAll(".passo"));
  const nodes = steps.map((step) => step.querySelector(".passo-nodo"));
  const panelBox = root.querySelector("[data-pannello]");
  const panels = Array.from(panelBox.querySelectorAll(".passo-dettagli"));
  const pause = document.querySelector(".percorso-pausa");
  const wide = matchMedia("(min-width: 48rem)"); // the same width as in style.css
  const lessMotion = matchMedia("(prefers-reduced-motion: reduce)");
  let current = -1;

  document.documentElement.classList.add("con-percorso");
  nodes.forEach((node) => (node.disabled = false));
  panels.forEach((panel) => (panel.querySelector(".passo-azioni").hidden = false));

  // Phones: the panel goes inside the chosen step, before its connection.
  // Wider screens: the panel goes back to its own place, next to or under the diagram.
  function placePanel() {
    if (!wide.matches) {
      const step = steps[current];
      step.insertBefore(panelBox, step.querySelector(".tratto"));
    } else if (panelBox.parentElement !== root) {
      root.append(panelBox);
    }
  }

  function show(index, byUser) {
    if (index === current) return;
    // The new text comes from the side you move to (Next: from the right).
    panelBox.dataset.direzione = index > current ? "avanti" : "indietro";
    current = index;
    nodes.forEach((node, i) => node.setAttribute("aria-expanded", String(i === index)));
    panels.forEach((panel, i) => {
      panel.hidden = i !== index;
      panel.classList.remove("entra");
    });
    placePanel();
    if (byUser) {
      void panels[index].offsetWidth; // restart the entrance animation
      panels[index].classList.add("entra");
      // The chosen step goes in the address (#passo-3), so the link can be shared.
      history.replaceState(null, "", "#" + panels[index].id);
    }
  }

  nodes.forEach((node, i) => {
    node.addEventListener("click", () => show(i, true));
    node.addEventListener("keydown", (event) => {
      const keys = { ArrowRight: i + 1, ArrowDown: i + 1, ArrowLeft: i - 1, ArrowUp: i - 1, Home: 0, End: nodes.length - 1 };
      if (!(event.key in keys)) return;
      event.preventDefault();
      const next = Math.min(Math.max(keys[event.key], 0), nodes.length - 1);
      show(next, true);
      nodes[next].focus();
    });
  });

  // Back / Next inside the panel.
  panelBox.addEventListener("click", (event) => {
    const button = event.target.closest("[data-vai]");
    if (!button) return;
    const target = Number(button.dataset.vai);
    const forward = target > current;
    show(target, true);
    // The old button is now hidden: keep the focus on the same kind of button,
    // so pressing Enter again goes on.
    const buttons = Array.from(panels[current].querySelectorAll("[data-vai]"));
    const same = buttons.find((b) => Number(b.dataset.vai) > current === forward);
    (same || buttons[0]).focus();
  });

  // Moving things must be easy to stop. With "reduce motion" nothing moves: no button needed.
  function updatePauseButton() {
    pause.hidden = lessMotion.matches;
  }
  pause.addEventListener("click", () => {
    const paused = root.classList.toggle("in-pausa");
    pause.textContent = paused ? "Riprendi" : "Pausa";
  });
  lessMotion.addEventListener("change", updatePauseButton);
  wide.addEventListener("change", placePanel);
  updatePauseButton();

  const fromAddress = panels.findIndex((panel) => "#" + panel.id === location.hash);
  show(fromAddress >= 0 ? fromAddress : 0, false);
})();
