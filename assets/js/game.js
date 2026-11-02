// Slot machine effect: numbers marked with data-spin show random digits for a moment
// before stopping on the real value. Used to reveal the answer.
function spinNumbers(root) {
  root.querySelectorAll("[data-spin]").forEach((element) => {
    const target = element.dataset.spin;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      element.textContent = target;
      return;
    }
    let ticks = 0;
    const timer = setInterval(() => {
      ticks += 1;
      if (ticks >= 14) {
        clearInterval(timer);
        element.textContent = target;
        return;
      }
      element.textContent = target.replace(/\d/g, () => Math.floor(Math.random() * 10));
    }, 60);
  });
}

// htmx.onLoad runs on the first page load and again for every piece HTMX swaps in.
htmx.onLoad(spinNumbers);

// "+ Añadir jugador": show the next hidden name box and remove the button when
// every box is showing. Without JavaScript the first boxes still work.
function addPlayer(button) {
  const next = document.querySelector("[data-player][hidden]");
  next.hidden = false;
  next.querySelector("input").focus();
  if (!document.querySelector("[data-player][hidden]")) {
    button.remove();
  }
}
