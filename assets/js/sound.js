// Chiptune sounds made with the Web Audio API: every blip, tune and bang is generated
// in the browser, so there are no audio files to download or license. Players can
// turn music and sound effects off in Opciones (no-music / no-sfx classes on <html>).
const Sound = (() => {
  let context = null;
  let master = null;
  let musicBus = null;
  let musicTimer = null;

  function enabled(kind) {
    return !document.documentElement.classList.contains(kind === "music" ? "no-music" : "no-sfx");
  }

  // Browsers only allow sound after the player touches the page, so the audio context
  // is created (or woken up) on the first tap.
  function audio() {
    if (!context) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      if (!AudioContext) {
        return null;
      }
      context = new AudioContext();
      master = context.createGain();
      master.gain.value = 0.25;
      master.connect(context.destination);
    }
    if (context.state === "suspended") {
      context.resume();
    }
    return context;
  }

  const frequency = (note) => 440 * 2 ** ((note - 69) / 12); // MIDI note number to Hz

  // One note: a wave that fades out. `slideTo` bends its pitch while it plays.
  function tone(hz, start, length, { type = "square", volume = 0.3, slideTo, out = master } = {}) {
    const oscillator = context.createOscillator();
    const gain = context.createGain();
    oscillator.type = type;
    oscillator.frequency.setValueAtTime(hz, start);
    if (slideTo) {
      oscillator.frequency.exponentialRampToValueAtTime(slideTo, start + length);
    }
    gain.gain.setValueAtTime(volume, start);
    gain.gain.exponentialRampToValueAtTime(0.001, start + length);
    oscillator.connect(gain).connect(out);
    oscillator.start(start);
    oscillator.stop(start + length + 0.05);
  }

  // Random noise through a filter: explosions, waves, a cheering crowd.
  function noise(start, length, { volume = 0.5, from = 2000, to = 100, filter = "lowpass" } = {}) {
    const buffer = context.createBuffer(1, Math.ceil(context.sampleRate * length), context.sampleRate);
    const samples = buffer.getChannelData(0);
    for (let i = 0; i < samples.length; i += 1) {
      samples[i] = Math.random() * 2 - 1;
    }
    const source = context.createBufferSource();
    const shape = context.createBiquadFilter();
    const gain = context.createGain();
    source.buffer = buffer;
    shape.type = filter;
    shape.frequency.setValueAtTime(from, start);
    shape.frequency.exponentialRampToValueAtTime(to, start + length);
    gain.gain.setValueAtTime(volume, start);
    gain.gain.exponentialRampToValueAtTime(0.001, start + length);
    source.connect(shape).connect(gain).connect(master);
    source.start(start);
  }

  // Music goes through its own volume knob, so it can be faded out at any moment.
  function newMusicBus() {
    stopMusic();
    musicBus = context.createGain();
    musicBus.connect(master);
    return musicBus;
  }

  function stopMusic() {
    clearTimeout(musicTimer);
    if (musicBus && context) {
      musicBus.gain.setTargetAtTime(0, context.currentTime, 0.1);
      musicBus = null;
    }
  }

  // Title screen: a short sea shanty in D minor, eight bars that loop.
  // Each note is [MIDI number, beats]; null is a rest.
  const SHANTY = [
    [62, 1], [62, 0.5], [64, 0.5], [65, 1], [69, 1],
    [67, 1], [65, 0.5], [64, 0.5], [62, 2],
    [60, 1], [60, 0.5], [62, 0.5], [64, 1], [65, 1],
    [64, 1], [62, 0.5], [61, 0.5], [62, 2],
    [69, 1], [69, 0.5], [70, 0.5], [69, 1], [67, 1],
    [65, 1], [64, 0.5], [65, 0.5], [67, 2],
    [69, 1], [67, 0.5], [65, 0.5], [64, 1], [61, 1],
    [62, 3], [null, 1],
  ];
  const SHANTY_BASS = [50, 46, 48, 45, 53, 46, 45, 50]; // one root note per bar
  const BEAT = 0.28; // seconds

  function titleMusic() {
    if (!audio() || !enabled("music")) {
      return;
    }
    const bus = newMusicBus();
    const loop = () => {
      const start = context.currentTime + 0.05;
      let time = start;
      for (const [note, beats] of SHANTY) {
        if (note) {
          tone(frequency(note), time, beats * BEAT * 0.9, { volume: 0.16, out: bus });
        }
        time += beats * BEAT;
      }
      SHANTY_BASS.forEach((note, bar) => {
        const barStart = start + bar * 4 * BEAT;
        const options = { type: "triangle", volume: 0.35, out: bus };
        tone(frequency(note), barStart, 2 * BEAT * 0.9, options);
        tone(frequency(note + 12), barStart + 2 * BEAT, 2 * BEAT * 0.9, options);
      });
      musicTimer = setTimeout(loop, (time - context.currentTime) * 1000);
    };
    loop();
  }

  // Reveal: a heartbeat that speeds up over a low note that keeps rising.
  function suspense(seconds) {
    if (!audio() || !enabled("music")) {
      return;
    }
    const bus = newMusicBus();
    const start = context.currentTime;
    let time = start;
    let gap = 0.6;
    while (time < start + seconds) {
      tone(80, time, 0.15, { type: "sine", volume: 0.7, slideTo: 40, out: bus });
      tone(70, time + 0.15, 0.12, { type: "sine", volume: 0.45, slideTo: 35, out: bus });
      time += gap;
      gap = Math.max(0.25, gap * 0.92);
    }
    const drone = { type: "sawtooth", volume: 0.05, slideTo: frequency(50), out: bus };
    tone(frequency(38), start, seconds, drone);
  }

  // End ceremony: a snare drum roll that grows louder, ending with a cymbal crash.
  function drumroll(seconds) {
    if (!audio() || !enabled("sfx")) {
      return;
    }
    stopMusic();
    const start = context.currentTime;
    for (let time = 0; time < seconds; time += 0.05) {
      const volume = 0.08 + 0.3 * (time / seconds); // crescendo
      noise(start + time, 0.05, { volume, from: 5000, to: 2500, filter: "bandpass" });
    }
    noise(start + seconds, 1.2, { volume: 0.4, from: 9000, to: 3000, filter: "highpass" });
  }

  // End ceremony: a short triumphant theme in C major for the winner, with a bass line.
  // Different on purpose from the fanfare of a ship sailing away.
  const VICTORY = [
    [67, 0.5], [67, 0.5], [67, 0.5], [72, 1.5],
    [70, 0.5], [72, 0.5], [74, 0.5], [76, 2],
    [74, 0.5], [76, 0.5], [77, 0.5], [79, 2.5],
  ];
  const VICTORY_BASS = [[48, 3], [46, 3.5], [43, 1.5], [48, 2.5]]; // as long as the melody
  const VICTORY_BEAT = 0.16; // seconds

  function victory() {
    if (!audio() || !enabled("sfx")) {
      return;
    }
    stopMusic();
    let time = context.currentTime;
    for (const [note, beats] of VICTORY) {
      tone(frequency(note), time, beats * VICTORY_BEAT * 0.95, { volume: 0.2 });
      tone(frequency(note - 12), time, beats * VICTORY_BEAT * 0.95, { type: "triangle", volume: 0.1 });
      time += beats * VICTORY_BEAT;
    }
    time = context.currentTime;
    for (const [note, beats] of VICTORY_BASS) {
      tone(frequency(note), time, beats * VICTORY_BEAT, { type: "triangle", volume: 0.35 });
      time += beats * VICTORY_BEAT;
    }
  }

  // A bright bell-like note, for each step of the podium.
  function ding(note) {
    if (!audio() || !enabled("sfx")) {
      return;
    }
    stopMusic();
    tone(frequency(note), context.currentTime, 0.5, { volume: 0.25 });
    tone(frequency(note + 12), context.currentTime, 0.5, { type: "triangle", volume: 0.15 });
  }

  function click() {
    if (!audio() || !enabled("sfx")) {
      return;
    }
    tone(frequency(84), context.currentTime, 0.06, { volume: 0.12, slideTo: frequency(91) });
  }

  // Shipwreck: a deep boom and a burst of noise that rumbles away.
  function explosion() {
    if (!audio() || !enabled("sfx")) {
      return;
    }
    const now = context.currentTime;
    noise(now, 1.6, { volume: 0.9, from: 4000, to: 60 });
    tone(90, now, 0.9, { type: "sine", volume: 0.9, slideTo: 25 });
  }

  // The ship sails away: a victory fanfare and a crowd cheering.
  function celebration() {
    if (!audio() || !enabled("sfx")) {
      return;
    }
    const now = context.currentTime;
    [72, 76, 79, 84].forEach((note, index) => {
      tone(frequency(note), now + index * 0.12, 0.14, { volume: 0.2 });
    });
    tone(frequency(84), now + 0.48, 0.6, { volume: 0.2 });
    tone(frequency(88), now + 0.48, 0.6, { volume: 0.12 });
    // Crowd: short bursts of filtered noise, like many voices shouting "hey!".
    for (let burst = 0; burst < 7; burst += 1) {
      const at = now + 0.3 + burst * 0.22 + Math.random() * 0.08;
      noise(at, 0.3, { volume: 0.35, from: 1600, to: 700, filter: "bandpass" });
    }
  }

  // Every tap: wake the audio up, start the title music once, and blip on buttons.
  let titleStarted = false;
  document.addEventListener(
    "pointerdown",
    (event) => {
      if (!audio()) {
        return;
      }
      if (!titleStarted && document.querySelector('[data-music="title"]')) {
        titleStarted = true;
        titleMusic();
      }
      if (event.target.closest("button, a")) {
        click();
      }
    },
    true,
  );

  return { suspense, stopMusic, explosion, celebration, ding, drumroll, victory };
})();
