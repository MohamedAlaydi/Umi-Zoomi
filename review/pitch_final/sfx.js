/* sfx.js: the sound set for the Umi Zoomi pitch deck.
   Everything is made in the browser with Web Audio. No audio files, nothing to download.
   The world is cut paper and wooden toys, so the sounds are wood, paper, a small bell
   and a toy xylophone. All of them are short and quiet.

   Use:
     SFX.unlock()            call inside the first key press or click (browsers need a gesture)
     SFX.play('alarm')       play a cue by name
     SFX.play('move', { dur: 1.5, dir: 'in' })
     SFX.toggle()            mute or unmute (bind it to the M key)
     SFX.history             list of { name, at } for every cue played (for tests)
     SFX.render(name, opts, seconds)   offline render, returns a Promise of an AudioBuffer
     SFX.cues                name -> { when, fn }  (the list the sound board shows)

   The tune: the three powers climb (C E G), the count steps down (G E D C),
   the pick lands on the top note, and the close resolves. One small melody across the talk. */
(function (root) {
  'use strict';

  var NOTE = { G4: 392.00, C5: 523.25, D5: 587.33, E5: 659.25, G5: 783.99, A5: 880.00, C6: 1046.50 };

  /* ---------- small helpers ---------- */
  function rng(seed) {
    return function () {
      seed |= 0; seed = seed + 0x6D2B79F5 | 0;
      var t = Math.imul(seed ^ seed >>> 15, 1 | seed);
      t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t;
      return ((t ^ t >>> 14) >>> 0) / 4294967296;
    };
  }
  var noiseCache = new WeakMap();
  function noiseBuffer(ctx) {
    var b = noiseCache.get(ctx);
    if (b) return b;
    var n = Math.floor(ctx.sampleRate * 2);
    b = ctx.createBuffer(1, n, ctx.sampleRate);
    var d = b.getChannelData(0), r = rng(14);
    for (var i = 0; i < n; i++) d[i] = r() * 2 - 1;
    noiseCache.set(ctx, b);
    return b;
  }
  var noiseTurn = 0;
  function noise(ctx, t, dur) {
    var s = ctx.createBufferSource();
    s.buffer = noiseBuffer(ctx); s.loop = true;
    noiseTurn = (noiseTurn + 0.371) % 1.5;
    s.start(t, noiseTurn); s.stop(t + dur);
    return s;
  }
  function env(ctx, t, peak, attack, decay) {
    var g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(Math.max(peak, 0.0002), t + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, t + attack + decay);
    return g;
  }
  function osc(ctx, type, freq, t, stopAt) {
    var o = ctx.createOscillator();
    o.type = type; o.frequency.setValueAtTime(freq, t);
    o.start(t); o.stop(stopAt);
    return o;
  }
  function filter(ctx, type, freq, q) {
    var f = ctx.createBiquadFilter();
    f.type = type; f.frequency.value = freq; if (q) f.Q.value = q;
    return f;
  }
  function pick(o, k, d) { return o && o[k] !== undefined ? o[k] : d; }

  /* ---------- instruments ---------- */

  // toy xylophone bar: a sine, its fourth partial, and a soft mallet tap
  function mallet(ctx, out, t, freq, o) {
    var gain = pick(o, 'gain', 0.34), decay = pick(o, 'decay', 0.5), bright = pick(o, 'bright', 0.2);
    var end = t + decay + 0.1;
    var g1 = env(ctx, t, gain, 0.004, decay); osc(ctx, 'sine', freq, t, end).connect(g1); g1.connect(out);
    var g2 = env(ctx, t, gain * bright, 0.003, decay * 0.3); osc(ctx, 'sine', freq * 4, t, end).connect(g2); g2.connect(out);
    var n = noise(ctx, t, 0.04), bp = filter(ctx, 'bandpass', 2200, 1.2), g3 = env(ctx, t, gain * 0.5, 0.001, 0.02);
    n.connect(bp); bp.connect(g3); g3.connect(out);
  }

  // wood block click
  function wood(ctx, out, t, o) {
    var f = pick(o, 'freq', 820), gain = pick(o, 'gain', 0.22), dur = pick(o, 'dur', 0.06);
    var end = t + dur + 0.05;
    var a = ctx.createOscillator(); a.type = 'sine';
    a.frequency.setValueAtTime(f, t); a.frequency.exponentialRampToValueAtTime(f * 0.72, t + dur);
    a.start(t); a.stop(end);
    var g1 = env(ctx, t, gain, 0.001, dur); a.connect(g1); g1.connect(out);
    var g2 = env(ctx, t, gain * 0.35, 0.001, dur * 0.4); osc(ctx, 'triangle', f * 2.42, t, end).connect(g2); g2.connect(out);
    var n = noise(ctx, t, 0.03), hp = filter(ctx, 'highpass', 2800), g3 = env(ctx, t, gain * 0.6, 0.001, 0.012);
    n.connect(hp); hp.connect(g3); g3.connect(out);
  }

  // one strike of a small desk bell
  function ding(ctx, out, t, o) {
    var f = pick(o, 'freq', 1318.5), gain = pick(o, 'gain', 0.15), decay = pick(o, 'decay', 0.9);
    var parts = [[1, 1, 1], [1.003, 0.5, 1], [2.0, 0.45, 0.7], [2.74, 0.3, 0.5], [3.76, 0.18, 0.35], [5.4, 0.1, 0.22]];
    for (var i = 0; i < parts.length; i++) {
      var p = parts[i], g = env(ctx, t, gain * p[1], 0.002, decay * p[2]);
      osc(ctx, 'sine', f * p[0], t, t + decay * p[2] + 0.1).connect(g); g.connect(out);
    }
    var n = noise(ctx, t, 0.03), hp = filter(ctx, 'highpass', 4500), g3 = env(ctx, t, gain * 0.9, 0.001, 0.008);
    n.connect(hp); hp.connect(g3); g3.connect(out);
  }

  // air moving past: the camera travels
  function whoosh(ctx, out, t, o) {
    var dur = pick(o, 'dur', 1.5), gain = pick(o, 'gain', 0.3), dirIn = pick(o, 'dir', 'in') !== 'out';
    var n = noise(ctx, t, dur + 0.05), bp = filter(ctx, 'bandpass', 400, 0.8), lp = filter(ctx, 'lowpass', 3200);
    var f0 = dirIn ? 260 : 1500, f1 = dirIn ? 1500 : 260;
    bp.frequency.setValueAtTime(f0, t); bp.frequency.exponentialRampToValueAtTime(f1, t + dur);
    var g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(gain, t + dur * 0.45);
    g.gain.linearRampToValueAtTime(0.0001, t + dur);
    n.connect(bp); bp.connect(lp); lp.connect(g); g.connect(out);
  }

  // many small wooden clicks spread over a moment: tiles leaving, pieces running
  function clicks(ctx, out, t, o) {
    var count = Math.max(1, Math.min(48, Math.round(pick(o, 'count', 24))));
    var dur = pick(o, 'dur', 0.75), gain = pick(o, 'gain', 0.13), lo = pick(o, 'lo', 520), hi = pick(o, 'hi', 1100);
    var r = rng(pick(o, 'seed', 7) * 101 + count);
    for (var i = 0; i < count; i++) {
      wood(ctx, out, t + r() * dur, { freq: lo + r() * (hi - lo), gain: gain * (0.45 + r() * 0.55), dur: 0.035 + r() * 0.03 });
    }
  }

  // a tape measure being pulled: fast clicks that speed up, then slow down
  function ratchet(ctx, out, t, o) {
    var dur = pick(o, 'dur', 1.1), count = Math.round(pick(o, 'count', 22)), gain = pick(o, 'gain', 0.09);
    for (var i = 0; i < count; i++) {
      var u = (i + 0.5) / count, e = u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2;   // same ease as the blade
      wood(ctx, out, t + e * dur, { freq: 1400 + 500 * u, gain: gain, dur: 0.018 });
    }
  }

  // a page turning, with the sheet landing at the end
  function page(ctx, out, t, o) {
    var dur = pick(o, 'dur', 0.9), gain = pick(o, 'gain', 0.3);
    var n = noise(ctx, t, dur + 0.05), bp = filter(ctx, 'bandpass', 2400, 0.7);
    bp.frequency.setValueAtTime(2400, t); bp.frequency.exponentialRampToValueAtTime(700, t + dur);
    var g = ctx.createGain();
    g.gain.setValueAtTime(0.0001, t);
    g.gain.linearRampToValueAtTime(gain, t + dur * 0.3);
    g.gain.linearRampToValueAtTime(gain * 0.5, t + dur * 0.7);
    g.gain.linearRampToValueAtTime(0.0001, t + dur);
    n.connect(bp); bp.connect(g); g.connect(out);
    var r = rng(31);
    for (var i = 0; i < 9; i++) paper(ctx, out, t + r() * dur * 0.8, { dur: 0.04, gain: gain * 0.35 });
    var land = t + dur * 0.92, a = ctx.createOscillator(); a.type = 'sine';
    a.frequency.setValueAtTime(120, land); a.frequency.exponentialRampToValueAtTime(70, land + 0.09);
    a.start(land); a.stop(land + 0.2);
    var gl = env(ctx, land, gain * 0.9, 0.004, 0.11); a.connect(gl); gl.connect(out);
  }

  // a short paper rustle: something folds up
  function paper(ctx, out, t, o) {
    var dur = pick(o, 'dur', 0.22), gain = pick(o, 'gain', 0.16);
    var n = noise(ctx, t, dur + 0.03), bp = filter(ctx, 'bandpass', 3400, 0.5), g = env(ctx, t, gain, dur * 0.3, dur * 0.7);
    n.connect(bp); bp.connect(g); g.connect(out);
  }

  // a low wooden knock: a gate closes
  function knock(ctx, out, t, o) {
    var f = pick(o, 'freq', 190), gain = pick(o, 'gain', 0.4);
    var a = ctx.createOscillator(); a.type = 'sine';
    a.frequency.setValueAtTime(f, t); a.frequency.exponentialRampToValueAtTime(f * 0.6, t + 0.08);
    a.start(t); a.stop(t + 0.2);
    var g = env(ctx, t, gain, 0.002, 0.1); a.connect(g); g.connect(out);
    wood(ctx, out, t, { freq: 640, gain: gain * 0.4, dur: 0.04 });
  }

  function seq(ctx, out, t, names, step, o) {
    for (var i = 0; i < names.length; i++) mallet(ctx, out, t + i * step, NOTE[names[i]], o);
  }

  /* ---------- cues: the only names a deck should call ---------- */
  var POWER = ['C5', 'E5', 'G5'], COUNT = ['G5', 'E5', 'D5', 'C5'], CARD = ['E5', 'G5', 'A5'];
  function idx(o, n) { return Math.max(0, Math.min(n - 1, Math.round(pick(o, 'i', 0)))); }

  var CUES = {
    alarm: { when: 'The pitch starts. The bell rings twice.', len: 2.2, fn: function (c, out, t) {
      ding(c, out, t, {}); ding(c, out, t + 0.17, { gain: 0.13 });
      ding(c, out, t + 0.62, {}); ding(c, out, t + 0.79, { gain: 0.13 });
    } },
    title: { when: 'The title lands.', len: 1.2, fn: function (c, out, t) {
      seq(c, out, t, ['C5', 'G5'], 0.12, { gain: 0.3, decay: 0.75 });
    } },
    move: { when: 'The camera travels. Rises going in, falls going out.', len: 1.8, fn: function (c, out, t, o) { whoosh(c, out, t, o); } },
    tick: { when: 'The ruler pointer reaches a new unit.', len: 0.3, fn: function (c, out, t) { wood(c, out, t, { freq: 900, gain: 0.2 }); } },
    power: { when: 'A power is named. Three notes that climb.', len: 0.9, fn: function (c, out, t, o) {
      mallet(c, out, t, NOTE[POWER[idx(o, 3)]], { decay: 0.6 });
    } },
    count: { when: 'The big number changes. Four notes that step down.', len: 0.9, fn: function (c, out, t, o) {
      mallet(c, out, t, NOTE[COUNT[idx(o, 4)]], { decay: 0.6 });
    } },
    cut: { when: 'A filter runs and pieces leave.', len: 1.2, fn: function (c, out, t, o) { clicks(c, out, t, o); } },
    tape: { when: 'The measuring tape pulls out.', len: 1.4, fn: function (c, out, t, o) { ratchet(c, out, t, o); } },
    card: { when: 'A card docks next to the pick.', len: 0.7, fn: function (c, out, t, o) {
      mallet(c, out, t, NOTE[CARD[idx(o, 3)]], { gain: 0.2, decay: 0.4 });
    } },
    pick: { when: 'The pick is shown. The tune lands on the top note.', len: 1.6, fn: function (c, out, t) {
      seq(c, out, t, ['C5', 'E5', 'G5', 'C6'], 0.1, { gain: 0.3, decay: 0.8 });
    } },
    done: { when: 'Thank you. The tune resolves.', len: 2.2, fn: function (c, out, t) {
      seq(c, out, t, ['G4', 'C5', 'E5', 'G5'], 0.12, { gain: 0.26, decay: 0.7 });
      mallet(c, out, t + 0.5, NOTE.C5, { gain: 0.26, decay: 1.2 });
      mallet(c, out, t + 0.5, NOTE.C6, { gain: 0.26, decay: 1.2 });
    } },
    page: { when: 'Book only. A page turns and lands.', len: 1.3, fn: function (c, out, t, o) { page(c, out, t, o); } },
    rise: { when: 'Book only. A paper piece folds up.', len: 0.4, fn: function (c, out, t, o) { paper(c, out, t, o); } },
    gate: { when: 'Machine only. A gate closes.', len: 0.4, fn: function (c, out, t, o) { knock(c, out, t, o); } },
    flow: { when: 'Machine only. Pieces run along the belt.', len: 1.8, fn: function (c, out, t, o) {
      clicks(c, out, t, { count: pick(o, 'count', 36), dur: pick(o, 'dur', 1.4), gain: 0.09, lo: 420, hi: 900, seed: pick(o, 'seed', 3) });
    } },
    back: { when: 'Going one step back. One quiet click, nothing more.', len: 0.3, fn: function (c, out, t) { wood(c, out, t, { freq: 520, gain: 0.12 }); } }
  };

  /* ---------- engine ---------- */
  var ctx = null, master = null, muted = false, volume = 0.8, history = [];

  function ensure() {
    if (ctx) return ctx;
    var AC = root.AudioContext || root.webkitAudioContext;
    if (!AC) return null;
    ctx = new AC();
    var comp = ctx.createDynamicsCompressor();          // a soft ceiling, so nothing ever clips
    comp.threshold.value = -10; comp.knee.value = 12; comp.ratio.value = 6; comp.attack.value = 0.003; comp.release.value = 0.2;
    master = ctx.createGain(); master.gain.value = muted ? 0 : volume;
    master.connect(comp); comp.connect(ctx.destination);
    return ctx;
  }

  var SFX = {
    cues: CUES,
    history: history,
    get muted() { return muted; },
    get state() { return ctx ? ctx.state : 'none'; },
    unlock: function () {
      var c = ensure();
      if (c && c.state === 'suspended') c.resume();
      return !!c;
    },
    play: function (name, opts) {
      history.push({ name: name, at: Math.round(performance.now()), opts: opts || null });
      var cue = CUES[name];
      if (!cue || !SFX.unlock()) return false;
      try { cue.fn(ctx, master, ctx.currentTime + 0.02, opts || {}); } catch (e) { console.warn('sfx', name, e); return false; }
      return true;
    },
    mute: function (on) {
      muted = !!on;
      if (master) master.gain.setTargetAtTime(muted ? 0 : volume, ctx.currentTime, 0.02);
      return muted;
    },
    toggle: function () { return SFX.mute(!muted); },
    setVolume: function (v) {
      volume = Math.max(0, Math.min(1, v));
      if (master && !muted) master.gain.setTargetAtTime(volume, ctx.currentTime, 0.02);
    },
    render: function (name, opts, seconds) {
      var cue = CUES[name], sr = 44100;
      var OAC = root.OfflineAudioContext || root.webkitOfflineAudioContext;
      var off = new OAC(1, Math.ceil(sr * (seconds || cue.len)), sr);
      var g = off.createGain(); g.gain.value = volume; g.connect(off.destination);
      cue.fn(off, g, 0.02, opts || {});
      return off.startRendering();
    }
  };

  root.SFX = SFX;
})(typeof window !== 'undefined' ? window : globalThis);
