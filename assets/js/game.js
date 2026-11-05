// Animations are off if the phone asks for less movement or the player turned them
// off in Opciones (saved in this browser with localStorage).
function animationsOn() {
  return (
    !window.matchMedia("(prefers-reduced-motion: reduce)").matches &&
    !document.documentElement.classList.contains("no-anim")
  );
}

// Opciones: switch something on or off (animations, music, sound effects) and remember
// the choice on this phone. Each option is a class on <html>: no-anim, no-music, no-sfx.
const OPTION_CLASSES = { animations: "no-anim", music: "no-music", sfx: "no-sfx" };

function toggleOption(name) {
  const off = document.documentElement.classList.toggle(OPTION_CLASSES[name]);
  if (name === "music" && off) {
    Sound.stopMusic();
  }
  try {
    localStorage.setItem(name, off ? "off" : "on");
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
  const answer = Number(overlay.dataset.answer);
  const bid = Number(overlay.dataset.bid);
  const success = bid <= answer; // the same rule as the engine (R20)
  if (!animationsOn()) {
    overlay.remove(); // the board underneath already shows the result
    playEnding(success, 0);
    startCeremony();
    return;
  }
  overlay.hidden = false;
  lockPage(true);
  Sound.suspense((800 + SUSPENSE_MS) / 1000);
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
    counter.classList.add(success ? "text-px-green" : "text-px-red");
    overlay.querySelector("[data-voyage]").classList.remove("voyage-wait");
    playEnding(success, 600); // in time with the ship sailing off or the explosion
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

// The suspense music stops: fanfare and cheers if the ship sails, a bang if it sinks.
function playEnding(success, delay) {
  Sound.stopMusic();
  setTimeout(success ? Sound.celebration : Sound.explosion, delay);
}

// Back to the board: replay the coins jumping, which happened hidden behind the scene.
// While a full screen scene is on top, the page behind can't scroll and is hidden, so
// nothing of the board peeks out at the edges.
function lockPage(locked) {
  document.documentElement.classList.toggle("overflow-hidden", locked);
  document.documentElement.classList.toggle("overlay-open", locked);
}

function closeReveal(overlay) {
  overlay.remove();
  lockPage(false);
  document.querySelectorAll("#board .animate-hop").forEach((element) => {
    element.getAnimations().forEach((animation) => {
      animation.cancel();
      animation.play();
    });
  });
  startCeremony();
}

// End of the game: after the last reveal, the podium ceremony. The page says when each
// part appears (CSS delays); here we only add the sounds and the confetti in time.
const CONFETTI_COLOURS = ["#ff004d", "#29adff", "#ffec27", "#00e436", "#ffa300", "#ff77a8"];

function startCeremony() {
  const ceremony = document.querySelector("[data-ceremony]");
  if (!ceremony) {
    return;
  }
  ceremony.hidden = false;
  lockPage(true);
  Sound.drumroll(1.5);
  setTimeout(() => Sound.ding(67), 1500); // 3rd place
  setTimeout(() => Sound.ding(72), 2600); // 2nd place
  setTimeout(() => {
    Sound.victory(); // the winner
    if (animationsOn()) {
      throwConfetti(ceremony.querySelector("[data-confetti]"));
    }
  }, 3800);
}

function throwConfetti(container) {
  for (let i = 0; i < 40; i += 1) {
    const piece = document.createElement("span");
    piece.className = "animate-fall absolute top-0 size-2";
    piece.style.left = `${Math.random() * 100}%`;
    piece.style.background = CONFETTI_COLOURS[i % CONFETTI_COLOURS.length];
    piece.style.animationDelay = `${Math.random() * 1.5}s`;
    piece.style.animationDuration = `${2.5 + Math.random() * 2}s`;
    piece.addEventListener("animationend", () => piece.remove()); // gone once it lands
    container.append(piece);
  }
}

htmx.onLoad(playReveal);

// A new treasure question is celebrated with fireworks the moment it's seen: when the
// board loads, or when the "pass the phone" curtain in front of it is closed.
function celebrateTreasure(root) {
  const picture = root.querySelector("[data-fireworks]");
  if (!picture || document.querySelector("[data-handoff]")) {
    return; // no treasure question, or it's still hidden behind the curtain
  }
  picture.classList.add("celebrating"); // torches and gold flicker for 3 seconds
  Sound.fireworks();
  if (animationsOn()) {
    launchFireworks();
  }
}

htmx.onLoad(celebrateTreasure);

// About a second of pixel fireworks: a few bursts of coloured squares flying out from
// random points in the top half of the screen, at the same times as their bangs.
const FIREWORK_TIMES = [0, 250, 500, 700]; // ms, the same as Sound.fireworks()

function launchFireworks() {
  const sky = document.createElement("div");
  sky.className = "pointer-events-none fixed inset-0 z-50 overflow-hidden";
  document.body.append(sky);
  FIREWORK_TIMES.forEach((time, burst) => {
    setTimeout(() => {
      const x = 15 + Math.random() * 70; // % of the screen width
      const y = 10 + Math.random() * 35; // % of the screen height
      const colour = CONFETTI_COLOURS[burst % CONFETTI_COLOURS.length];
      for (let i = 0; i < 14; i += 1) {
        const spark = document.createElement("span");
        spark.className = "absolute size-2";
        spark.style.left = `${x}%`;
        spark.style.top = `${y}%`;
        spark.style.background = i % 4 === 0 ? "#fff1e8" : colour;
        const angle = (i / 14) * 2 * Math.PI;
        const distance = 50 + Math.random() * 30;
        const dx = Math.round(Math.cos(angle) * distance);
        const dy = Math.round(Math.sin(angle) * distance);
        spark.animate(
          [
            { transform: "translate(0, 0)", opacity: 1 },
            { transform: `translate(${dx}px, ${dy + 20}px)`, opacity: 0 }, // falls a bit
          ],
          { duration: 700, easing: "steps(7)", fill: "forwards" },
        );
        sky.append(spark);
      }
    }, time);
  });
  setTimeout(() => sky.remove(), 1600);
}
