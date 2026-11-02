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

// Reveal with suspense: the answer is counted up from 0, slowing down at the end. The
// ship waits at the dock until the counter stops on the real number: only then does it
// sail away (the bid made it) or blow up and sink.
const SUSPENSE_MS = 4500;
const MAX_STEPS = 40;

function playReveal(root) {
  const overlay = root.querySelector("[data-reveal]");
  if (!overlay) {
    return;
  }
  if (!animationsOn()) {
    overlay.remove(); // the board underneath already shows the result
    return;
  }
  overlay.hidden = false;

  const answer = Number(overlay.dataset.answer);
  const bid = Number(overlay.dataset.bid);
  const counter = overlay.querySelector("[data-count]");
  const steps = countingSteps(answer);
  const delays = stepDelays(steps.length);
  let index = 0;

  function next() {
    if (index < steps.length) {
      counter.textContent = steps[index];
      setTimeout(next, delays[index]);
      index += 1;
      return;
    }
    const success = bid <= answer; // the same rule as the engine (R20)
    counter.classList.add(success ? "text-px-green" : "text-px-red");
    overlay.querySelector("[data-voyage]").classList.remove("voyage-wait");
    // Once the ship has sailed or sunk, go straight to the scores.
    setTimeout(() => closeReveal(overlay), 3500);
  }
  // A short pause before counting, like a drum roll.
  setTimeout(next, 800);
}

// The numbers the counter shows. Small answers go one by one (1, 2, 3...); big ones
// take big jumps at first and smaller ones near the end, in at most MAX_STEPS steps.
function countingSteps(answer) {
  if (answer <= MAX_STEPS) {
    return Array.from({ length: answer + 1 }, (_, number) => number);
  }
  const steps = [0];
  for (let step = 1; step <= MAX_STEPS; step += 1) {
    const value = Math.round(answer * (1 - (1 - step / MAX_STEPS) ** 3));
    if (value > steps.at(-1)) {
      steps.push(value);
    }
  }
  return steps;
}

// How long each number stays on screen: short at first, longer and longer at the end,
// adding up to SUSPENSE_MS whatever the number of steps.
function stepDelays(count) {
  const weights = Array.from({ length: count }, (_, i) => 0.3 + 2 * (i / count) ** 2);
  const total = weights.reduce((sum, weight) => sum + weight, 0);
  return weights.map((weight) => (SUSPENSE_MS * weight) / total);
}

// Back to the board: replay the coins jumping, which happened hidden behind the scene.
function closeReveal(overlay) {
  overlay.remove();
  document.querySelectorAll("#board .animate-hop").forEach((element) => {
    element.getAnimations().forEach((animation) => {
      animation.cancel();
      animation.play();
    });
  });
}

htmx.onLoad(playReveal);
