/* umi-extras.js : extra props for the toy sorting machine scene.
   Plain classic script. Defines window.UMI.
   Every builder: (THREE, parent, api, opts) -> THREE.Group, already added to parent.
   api = { C, toneMaterial, Kit, round, flatInk, LIGHT }  (see deck) */
(function () {
  'use strict';

  var UMI = window.UMI || {};
  var texCache = {};      // base pattern / digit textures, built once
  var repCache = {};      // pattern textures per repeat value

  function rgb(hex) { return [(hex >> 16) & 255, (hex >> 8) & 255, hex & 255]; }
  function css(hex) { return '#' + ('000000' + (hex >>> 0).toString(16)).slice(-6); }
  function num(v, d) { return (typeof v === 'number' && isFinite(v)) ? v : d; }
  function srgb(THREE, tex) { if (THREE.SRGBColorSpace) tex.colorSpace = THREE.SRGBColorSpace; return tex; }

  /* ---------- patterns: two flat colours, hard edges, per pixel ---------- */
  var PATTERNS = {
    dots: function (u, v) {
      var a = u - 0.5, b = v - 0.5;
      if (a * a + b * b < 0.06) return 1;
      a = u < 0.5 ? u : u - 1; b = v < 0.5 ? v : v - 1;
      return (a * a + b * b < 0.06) ? 1 : 0;
    },
    stripes: function (u) { return u < 0.5 ? 1 : 0; },
    zigzag: function (u, v) {
      var tri = Math.abs(u * 2 - 1);
      var f = (v + tri * 0.5) % 1;
      return f < 0.5 ? 1 : 0;
    },
    check: function (u, v) { return ((u < 0.5) !== (v < 0.5)) ? 1 : 0; }
  };

  function basePattern(THREE, kind, a, b) {
    if (!PATTERNS[kind]) kind = 'dots';
    var key = kind + '|' + a + '|' + b;
    if (texCache[key]) return texCache[key];
    var S = 64, c = document.createElement('canvas');
    c.width = c.height = S;
    var ctx = c.getContext('2d'), img = ctx.createImageData(S, S);
    var ca = rgb(a), cb = rgb(b), fn = PATTERNS[kind];
    for (var y = 0; y < S; y++) {
      for (var x = 0; x < S; x++) {
        var col = fn((x + 0.5) / S, (y + 0.5) / S) ? cb : ca, i = (y * S + x) * 4;
        img.data[i] = col[0]; img.data[i + 1] = col[1]; img.data[i + 2] = col[2]; img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
    var tex = new THREE.CanvasTexture(c);
    tex.magFilter = THREE.NearestFilter;
    tex.minFilter = THREE.LinearMipmapLinearFilter;
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    srgb(THREE, tex);
    texCache[key] = tex;
    return tex;
  }

  /* a pattern texture with its own repeat; shares the canvas with the base one */
  function patternTexture(THREE, kind, a, b, rx, ry) {
    rx = rx || 1; ry = ry || 1;
    var base = basePattern(THREE, kind, a, b);
    if (rx === 1 && ry === 1) return base;
    var key = kind + '|' + a + '|' + b + '|' + rx + '|' + ry;
    if (repCache[key]) return repCache[key];
    var t = base.clone();
    t.repeat.set(rx, ry);
    t.needsUpdate = true;
    repCache[key] = t;
    return t;
  }
  UMI.patternTexture = function (THREE, kind, colors, rx, ry) {
    return patternTexture(THREE, kind, colors[0], colors[1], rx, ry);
  };

  /* ---------- small geometry helpers ---------- */
  /* convex polygon (CCW points in XY) extruded along z, flat normals, non indexed */
  function prism(THREE, pts, t, ox, oy, oz, out) {
    var P = out || { p: [], n: [] }, h = t / 2, n = pts.length, i;
    ox = ox || 0; oy = oy || 0; oz = oz || 0;
    function v(pt, z, nx, ny, nz) { P.p.push(pt[0] + ox, pt[1] + oy, z + oz); P.n.push(nx, ny, nz); }
    for (i = 1; i < n - 1; i++) {
      v(pts[0], h, 0, 0, 1); v(pts[i], h, 0, 0, 1); v(pts[i + 1], h, 0, 0, 1);
      v(pts[0], -h, 0, 0, -1); v(pts[i + 1], -h, 0, 0, -1); v(pts[i], -h, 0, 0, -1);
    }
    for (i = 0; i < n; i++) {
      var a = pts[i], b = pts[(i + 1) % n];
      var dx = b[0] - a[0], dy = b[1] - a[1], l = Math.sqrt(dx * dx + dy * dy) || 1;
      var nx = dy / l, ny = -dx / l;
      v(a, h, nx, ny, 0); v(a, -h, nx, ny, 0); v(b, -h, nx, ny, 0);
      v(a, h, nx, ny, 0); v(b, -h, nx, ny, 0); v(b, h, nx, ny, 0);
    }
    return P;
  }
  function prismGeometry(THREE, P) {
    var g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(P.p, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(P.n, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(new Array(P.p.length / 3 * 2).fill(0), 2));
    return g;
  }
  /* flat convex polygon facing +z, uv = xy in world units so patterns keep one scale */
  function flatPoly(THREE, pts) {
    var p = [], nn = [], uv = [];
    for (var i = 1; i < pts.length - 1; i++) {
      [pts[0], pts[i], pts[i + 1]].forEach(function (q) { p.push(q[0], q[1], 0); nn.push(0, 0, 1); uv.push(q[0], q[1]); });
    }
    var g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(p, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(nn, 3));
    g.setAttribute('uv', new THREE.Float32BufferAttribute(uv, 2));
    return g;
  }
  function ngon(n, r, rot) {
    var pts = [];
    for (var i = 0; i < n; i++) { var a = rot + i / n * Math.PI * 2; pts.push([Math.cos(a) * r, Math.sin(a) * r]); }
    return pts;
  }
  function sub(THREE, parent, x, y, z) {
    var g = new THREE.Group(); g.position.set(x || 0, y || 0, z || 0); parent.add(g); return g;
  }
  function root(THREE, parent, name, opts, scale) {
    var g = new THREE.Group();
    g.name = name;
    g.position.set(num(opts.x, 0), num(opts.y, 0), num(opts.z, 0));
    if (scale && scale !== 1) g.scale.setScalar(scale);
    parent.add(g);
    return g;
  }

  /* ====================================================================
     1. patternDecal
     opts { kind:'dots'|'stripes'|'zigzag'|'check', colors:[a,b], x,y,z, w,d,
            rotX, rotY, repeat (number of cells across w, or [rx,ry]), border }
     Lies flat facing up. rotX = Math.PI/2 stands it up facing +z, rotY then turns it.
     x,y,z is the centre of the panel; put it ON the surface, it lifts itself 0.02.
     ==================================================================== */
  UMI.patternDecal = function (THREE, parent, api, opts) {
    opts = opts || {};
    var C = api.C, w = num(opts.w, 1), d = num(opts.d, 1);
    var cols = opts.colors || [C.card, C.blue];
    var rx, ry;
    if (Array.isArray(opts.repeat)) { rx = opts.repeat[0]; ry = opts.repeat[1]; }
    else {
      rx = opts.repeat ? opts.repeat : Math.max(1, Math.round(w / 0.3));
      ry = Math.max(1, Math.round(rx * d / w));
    }
    var border = num(opts.border, 0.05);
    var g = root(THREE, parent, 'umi-patternDecal', opts);
    g.rotation.order = 'YXZ';
    g.rotation.set(num(opts.rotX, 0), num(opts.rotY, 0), 0);

    if (border > 0) {
      var bg = new THREE.PlaneGeometry(w + border * 2, d + border * 2); bg.rotateX(-Math.PI / 2);
      var rim = new THREE.Mesh(bg, api.flatInk);
      rim.position.y = 0.01;
      g.add(rim);
    }
    var pg = new THREE.PlaneGeometry(w, d); pg.rotateX(-Math.PI / 2);
    var mat = api.toneMaterial({ map: patternTexture(THREE, opts.kind || 'dots', cols[0], cols[1], rx, ry) });
    mat.polygonOffset = true; mat.polygonOffsetFactor = -2; mat.polygonOffsetUnits = -2;
    var face = new THREE.Mesh(pg, mat);
    face.position.y = 0.02;
    g.add(face);
    g.face = face;
    return g;
  };

  /* ====================================================================
     2. pegTeam
     opts { x,y,z, spacing (0.42), scale (1) }
     group.walkTo(x,y,z,seconds), group.step(now)  now = ms (rAF time), call each frame.
     group.pegs = the five sub groups, group.walking = bool.
     ==================================================================== */
  UMI.pegTeam = function (THREE, parent, api, opts) {
    opts = opts || {};
    var C = api.C, s = num(opts.scale, 1), spacing = num(opts.spacing, 0.42);
    var g = root(THREE, parent, 'umi-pegTeam', opts, s);
    var defs = [
      { c: C.red, b: C.card, head: 'sphere', kind: 'dots' },
      { c: C.blue, b: C.card, head: 'box', kind: 'stripes' },
      { c: C.yellow, b: C.ink, head: 'cone', kind: 'check' },
      { c: C.green, b: C.card, head: 'cylinder', kind: 'zigzag' },
      { c: C.ink, b: C.yellow, head: 'hexagon', kind: 'dots' }
    ];
    var BH = 0.44;                                         // body height
    var HEX = [[0.17, 0], [0.075, 0.135], [-0.075, 0.135], [-0.17, 0], [-0.075, -0.135], [0.075, -0.135]];
    var bodyGeo = new THREE.CylinderGeometry(0.105, 0.15, BH, 18, 3); bodyGeo.translate(0, BH / 2, 0);
    var bandGeo = new THREE.CylinderGeometry(0.126, 0.142, 0.16, 18, 1, true); bandGeo.translate(0, 0.2, 0);
    var eyeGeo = new THREE.CircleGeometry(0.03, 10);
    var shadowKit = new api.Kit();
    g.pegs = [];

    defs.forEach(function (df, i) {
      var px = (i - (defs.length - 1) / 2) * spacing;
      var peg = sub(THREE, g, px, 0, 0);
      peg.userData.baseX = px;
      api.round(peg, bodyGeo, df.c, 0, 0, 0, 0);
      var band = new THREE.Mesh(bandGeo, api.toneMaterial({ map: patternTexture(THREE, df.kind, df.c, df.b, 6, 1) }));
      peg.add(band);

      var ey = BH + 0.14, ez = 0.15, ex = 0.055;
      if (df.head === 'sphere') {
        api.round(peg, new THREE.SphereGeometry(0.155, 18, 12), C.wood, 0.155, 0, BH + 0.14, 0);
        ez = 0.148;
      } else if (df.head === 'box') {
        var hk = new api.Kit();
        hk.box(0, BH, 0, 0.27, 0.27, 0.27, C.wood);
        hk.build(peg);
        ey = BH + 0.14; ez = 0.135;
      } else if (df.head === 'cone') {
        api.round(peg, new THREE.ConeGeometry(0.175, 0.32, 18), C.wood, 0, 0, BH + 0.16, 0);
        ey = BH + 0.09; ez = 0.126; ex = 0.05;
      } else if (df.head === 'cylinder') {
        api.round(peg, new THREE.CylinderGeometry(0.15, 0.15, 0.25, 18, 2), C.wood, 0, 0, BH + 0.125, 0);
        ey = BH + 0.13; ez = 0.14;
      } else {
        api.round(peg, prismGeometry(THREE, prism(THREE, HEX, 0.22)), C.wood, 0, 0, BH + 0.135, 0);
        ey = BH + 0.13; ez = 0.11;
      }
      [-ex, ex].forEach(function (x) {
        var e = new THREE.Mesh(eyeGeo, api.flatInk);
        e.position.set(x, ey, ez + 0.008);
        peg.add(e);
      });
      shadowKit.box(px, 0, 0, 0.22, 0.02, 0.22, C.ink, { ink: false, shadow: 0.2 });
      g.pegs.push(peg);
    });
    shadowKit.build(g);

    var walk = null;
    g.walking = false;
    g.walkTo = function (x, y, z, seconds) {
      var to = new THREE.Vector3(num(x, g.position.x), num(y, g.position.y), num(z, g.position.z));
      if (!(seconds > 0)) { g.position.copy(to); walk = null; g.walking = false; settle(); return g; }
      walk = { from: g.position.clone(), to: to, dur: seconds * 1000, t0: null };
      g.walking = true;
      return g;
    };
    function settle() { for (var i = 0; i < g.pegs.length; i++) g.pegs[i].position.y = 0; }
    g.step = function (now) {
      if (!walk) return;
      if (now == null) now = performance.now();
      if (walk.t0 == null) walk.t0 = now;
      var t = Math.min(1, Math.max(0, (now - walk.t0) / walk.dur));
      var e = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
      g.position.lerpVectors(walk.from, walk.to, e);
      var steps = Math.max(2, Math.round(walk.from.distanceTo(walk.to) / (0.5 * s)));
      var amp = 0.045 * Math.sin(Math.PI * t);               // fades in and out
      for (var i = 0; i < g.pegs.length; i++) {
        g.pegs[i].position.y = amp * Math.abs(Math.sin(Math.PI * (t * steps + i * 0.5)));
      }
      if (t >= 1) { walk = null; g.walking = false; settle(); }
    };
    return g;
  };

  /* ====================================================================
     3. powerEmblems
     opts { x,y,z, gap (1.5), scale (1), pattern (false) }   circle red, triangle blue, square green
     ==================================================================== */
  UMI.powerEmblems = function (THREE, parent, api, opts) {
    opts = opts || {};
    var C = api.C, s = num(opts.scale, 1), gap = num(opts.gap, 1.5);
    var g = root(THREE, parent, 'umi-powerEmblems', opts, s);
    var T = 0.12, BH = 0.1, k = new api.Kit();
    var defs = [
      { shape: 'circle', c: C.red, kind: 'dots' },
      { shape: 'triangle', c: C.blue, kind: 'zigzag' },
      { shape: 'square', c: C.green, kind: 'check' }
    ];
    g.emblems = [];
    defs.forEach(function (df, i) {
      var cx = (i - 1) * gap, cy, inner, e;
      k.box(cx, 0, 0, 0.92, BH, 0.36, C.wood, { shadow: 0.3 });
      if (df.shape === 'circle') {
        var cg = new THREE.CylinderGeometry(0.4, 0.4, T, 36); cg.rotateX(Math.PI / 2);
        cy = BH + 0.39;
        e = sub(THREE, g, cx, cy, 0);
        api.round(e, cg, df.c, 0, 0, 0, 0);
        inner = ngon(36, 0.24, 0);
      } else if (df.shape === 'triangle') {
        cy = BH + 0.26;
        e = sub(THREE, g, cx, cy, 0);
        api.round(e, prismGeometry(THREE, prism(THREE, [[0, 0.56], [-0.42, -0.26], [0.42, -0.26]], T)), df.c, 0, 0, 0, 0);
        inner = [[0, 0.27], [-0.2, -0.12], [0.2, -0.12]];
      } else {
        cy = BH + 0.38;
        k.box(cx, BH, 0, 0.76, 0.76, T, df.c);
        e = sub(THREE, g, cx, cy, 0);
        inner = [[-0.22, -0.22], [0.22, -0.22], [0.22, 0.22], [-0.22, 0.22]];
      }
      var mat = api.toneMaterial(opts.pattern
        ? { map: patternTexture(THREE, df.kind, C.card, df.c, 4, 4) }
        : { color: C.card });
      mat.polygonOffset = true; mat.polygonOffsetFactor = -2; mat.polygonOffsetUnits = -2;
      var face = new THREE.Mesh(flatPoly(THREE, inner), mat);
      face.position.z = T / 2 + 0.012;
      e.add(face);
      g.emblems.push(e);
    });
    k.build(g);
    return g;
  };

  /* ====================================================================
     4. ruler
     opts { x,y,z, length (6), rotY (0), t (0) }
     group.setPointer(t)  t = 0..1 along the ruler.  group.pointer = the red block.
     ==================================================================== */
  UMI.ruler = function (THREE, parent, api, opts) {
    opts = opts || {};
    var C = api.C, L = num(opts.length, 6), D = 0.56, H = 0.1;
    var g = root(THREE, parent, 'umi-ruler', opts);
    g.rotation.y = num(opts.rotY, 0);
    var k = new api.Kit();
    k.box(0, 0, 0, L, H, D, C.wood, { shadow: 0.2 });
    var margin = 0.2, usable = L - margin * 2;
    var n = Math.max(1, Math.round(usable / 0.25)), stepX = usable / n;
    for (var i = 0; i <= n; i++) {
      var major = i % 4 === 0, dep = major ? 0.3 : 0.15;
      k.box(-usable / 2 + i * stepX, H, D / 2 - 0.04 - dep / 2, 0.055, 0.012, dep, C.ink, { ink: false });
    }
    k.build(g);

    var p = sub(THREE, g, 0, 0, 0);
    var pk = new api.Kit();
    pk.box(0, 0, 0, 0.28, 0.36, D + 0.2, C.red, { shadow: 0.2 });
    pk.box(0, 0.36, 0, 0.06, 0.012, D + 0.2, C.ink, { ink: false });
    pk.build(p);
    g.pointer = p;
    g.setPointer = function (t) {
      t = Math.min(1, Math.max(0, num(t, 0)));
      p.position.x = (t - 0.5) * usable;
      g.pointerT = t;
      return g;
    };
    g.setPointer(num(opts.t, 0));
    return g;
  };

  /* ====================================================================
     5. numberTiles
     opts { text ('40'), x,y,z, scale (1), gap (0.08), color (card), align:'center'|'left' }
     group.setText(str) swaps the digits (cheap when the length is the same).
     Characters: 0-9, '-', '.', ':', space.  Digits are drawn as canvas strokes, no font.
     ==================================================================== */
  var GLYPH = {
    '0': function (c) { c.ellipse(50, 70, 27, 48, 0, 0, Math.PI * 2); },
    '1': function (c) { c.moveTo(30, 42); c.lineTo(56, 22); c.lineTo(56, 122); },
    '2': function (c) { c.moveTo(22, 50); c.arc(50, 50, 28, Math.PI, Math.PI * 2); c.lineTo(26, 118); c.lineTo(82, 118); },
    '3': function (c) { c.moveTo(22, 22); c.lineTo(76, 22); c.lineTo(46, 60); c.arc(46, 90, 30, -Math.PI / 2, Math.PI * 0.78); },
    '4': function (c) { c.moveTo(64, 124); c.lineTo(64, 20); c.lineTo(20, 92); c.lineTo(86, 92); },
    '5': function (c) { c.moveTo(78, 22); c.lineTo(30, 22); c.lineTo(28, 62); c.arc(46, 88, 31.5, -2.17, 2.5); },
    '6': function (c) { c.moveTo(68, 18); c.quadraticCurveTo(22, 40, 21, 90); c.moveTo(79, 90); c.arc(50, 90, 29, 0, Math.PI * 2); },
    '7': function (c) { c.moveTo(20, 22); c.lineTo(80, 22); c.lineTo(44, 124); },
    '8': function (c) { c.moveTo(72, 44); c.arc(50, 44, 22, 0, Math.PI * 2); c.moveTo(78, 94); c.arc(50, 94, 28, 0, Math.PI * 2); },
    '9': function (c) { c.moveTo(79, 50); c.arc(50, 50, 29, 0, Math.PI * 2); c.moveTo(79, 50); c.quadraticCurveTo(78, 100, 32, 122); },
    '-': function (c) { c.moveTo(24, 70); c.lineTo(76, 70); },
    '.': function (c) { c.rect(44, 106, 12, 12); },
    ':': function (c) { c.rect(44, 40, 12, 12); c.rect(44, 92, 12, 12); }
  };
  function digitTexture(THREE, ch, bg, fg) {
    var key = 'digit|' + ch + '|' + bg + '|' + fg;
    if (texCache[key]) return texCache[key];
    var c = document.createElement('canvas');
    c.width = 100; c.height = 140;
    var ctx = c.getContext('2d');
    ctx.fillStyle = css(bg); ctx.fillRect(0, 0, 100, 140);
    if (GLYPH[ch]) {
      ctx.strokeStyle = css(fg); ctx.lineWidth = 19; ctx.lineCap = 'butt'; ctx.lineJoin = 'miter'; ctx.miterLimit = 3;
      ctx.beginPath(); GLYPH[ch](ctx); ctx.stroke();
    }
    var tex = new THREE.CanvasTexture(c);
    tex.generateMipmaps = false;
    tex.minFilter = THREE.LinearFilter; tex.magFilter = THREE.LinearFilter;
    srgb(THREE, tex);
    texCache[key] = tex;
    return tex;
  }

  UMI.numberTiles = function (THREE, parent, api, opts) {
    opts = opts || {};
    var C = api.C, s = num(opts.scale, 1), gap = num(opts.gap, 0.08);
    var bg = num(opts.color, C.card);
    var W = 0.72, H = 0.96, D = 0.2, RIM = 0.07;
    var g = root(THREE, parent, 'umi-numberTiles', opts, s);
    var faceGeo = new THREE.PlaneGeometry(W - RIM * 2, H - RIM * 2);
    var faces = [];
    g.text = '';

    function build(text) {
      while (g.children.length) {
        var ch = g.children[0]; g.remove(ch);
        if (ch.isInstancedMesh && ch.dispose) ch.dispose();
      }
      faces.forEach(function (f) { f.material.dispose(); });
      faces = [];
      var n = text.length, pitch = W + gap;
      var x0 = opts.align === 'left' ? W / 2 : -(n - 1) * pitch / 2;
      var k = new api.Kit();
      for (var i = 0; i < n; i++) {
        var cx = x0 + i * pitch;
        k.box(cx, 0, 0, W, H, D, C.wood, { shadow: 0.3 });
        var mat = api.toneMaterial({ map: digitTexture(THREE, text[i], bg, C.ink) });
        mat.polygonOffset = true; mat.polygonOffsetFactor = -2; mat.polygonOffsetUnits = -2;
        var f = new THREE.Mesh(faceGeo, mat);
        f.position.set(cx, H / 2, D / 2 + 0.012);
        faces.push(f);
      }
      if (n) k.build(g);
      faces.forEach(function (f) { g.add(f); });
    }
    g.setText = function (text) {
      text = String(text == null ? '' : text);
      if (text === g.text) return g;
      if (text.length === faces.length && faces.length) {
        for (var i = 0; i < text.length; i++) faces[i].material.map = digitTexture(THREE, text[i], bg, C.ink);
      } else build(text);
      g.text = text;
      return g;
    };
    g.setText(opts.text == null ? '40' : opts.text);
    return g;
  };

  /* ====================================================================
     6. bunting
     opts { x,y,z, width (8), count (9), poles (true), poleHeight (1.6), colors }
     x,y,z = middle of the string. Flags hang down 0.4 from y. Poles go down poleHeight.
     ==================================================================== */
  UMI.bunting = function (THREE, parent, api, opts) {
    opts = opts || {};
    var C = api.C, width = num(opts.width, 8), count = Math.max(1, Math.round(num(opts.count, 9)));
    var cols = opts.colors || [C.red, C.blue, C.yellow, C.green];
    var g = root(THREE, parent, 'umi-bunting', opts);
    var pitch = width / count, fw = Math.min(0.38, pitch * 0.72), fh = fw * 1.1;
    var tri = [[-fw / 2, 0], [0, -fh], [fw / 2, 0]];
    var byCol = cols.map(function () { return null; });
    for (var i = 0; i < count; i++) {
      var ci = i % cols.length;
      byCol[ci] = prism(THREE, tri, 0.04, -width / 2 + (i + 0.5) * pitch, -0.02, 0.045, byCol[ci]);
    }
    byCol.forEach(function (P, ci) {
      if (P) api.round(g, prismGeometry(THREE, P), cols[ci], 0, 0, 0, 0);
    });
    var k = new api.Kit();
    k.box(0, -0.025, 0, width, 0.05, 0.05, C.ink, { ink: false });
    if (opts.poles !== false) {
      var ph = num(opts.poleHeight, 1.6);
      k.box(-width / 2, -ph, 0, 0.14, ph + 0.14, 0.14, C.wood, { shadow: 0.3 });
      k.box(width / 2, -ph, 0, 0.14, ph + 0.14, 0.14, C.wood, { shadow: 0.3 });
    }
    k.build(g);
    return g;
  };

  window.UMI = UMI;
})();
