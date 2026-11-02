// Animations are off if the phone asks for less movement or the player turned them
// off in Opciones (saved in this browser with localStorage).
function animationsOn() {
  return (
    !window.matchMedia("(prefers-reduced-motion: reduce)").matches &&
    !document.documentElement.classList.contains("no-anim")
  );
}

// Opciones: switch animations on or off and remember the choice on this phone.
function toggleAnimations() {
  const off = document.documentElement.classList.toggle("no-anim");
  try {
    localStorage.setItem("animations", off ? "off" : "on");
  } catch {
    // Private browsing can block localStorage: the switch still works until reload.
  }
}

// Slot machine effect: numbers marked with data-spin show random digits for a moment
// before stopping on the real value. Used to reveal the answer.
function spinNumbers(root) {
  root.querySelectorAll("[data-spin]").forEach((element) => {
    const target = element.dataset.spin;
    if (!animationsOn()) {
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
  // Its default colour may have been picked by someone else meanwhile.
  if (coloursTaken(next).includes(colourInput(next).value)) {
    cycleColour(next.querySelector("button"));
  }
  next.querySelector("input").focus();
  if (!document.querySelector("[data-player][hidden]")) {
    button.remove();
  }
}

// Player colours: the square next to each name. Tapping it gives that player the next
// colour in the list that no other visible player has, so colours never repeat.
function cycleColour(button) {
  const row = button.closest("[data-player]");
  const input = colourInput(row);
  const colours = JSON.parse(document.getElementById("player-colours").textContent);
  const keys = colours.map(([key]) => key);
  const taken = coloursTaken(row);
  const start = keys.indexOf(input.value);
  for (let step = 1; step <= keys.length; step += 1) {
    const [key, background, text] = colours[(start + step) % keys.length];
    if (!taken.includes(key)) {
      input.value = key;
      button.style.background = background;
      button.style.color = text;
      return;
    }
  }
}

function colourInput(row) {
  return row.querySelector('input[type="hidden"]');
}

// Colours of the other players that are showing on screen.
function coloursTaken(row) {
  return [...document.querySelectorAll("[data-player]:not([hidden])")]
    .filter((other) => other !== row)
    .map((other) => colourInput(other).value);
}
