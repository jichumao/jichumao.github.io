/* The timeline page.
   The list runs newest first. Beside it (on wide screens) a dotted globe turns to the series in the middle of the
   screen and shows the journey up to that series, in the order it happened: every place visited by then is lit, an
   arc runs from each to the next, and the current one pulses. Moving up the list (forward in time) the newest leg
   draws itself in towards the current place; moving down (back in time) it pulls back into it.
   On narrow screens the globe sits above the list, turns slowly and shows every place.
   Series made at nearly the same spot (five around the Bay Area, three in Guangdong) would sit on top of each other,
   so each spot is one anchor and its series are numbered pins fanned out around it. The numbers are the series'
   order in time (1 is the oldest), the same numbers as in the list.
   The globe's land is a Fibonacci lattice of points; which of them are land comes in #tl-data (tools/footprint.py). */
(function () {
  var stops = Array.prototype.slice.call(document.querySelectorAll(".stop"));
  var now = document.querySelector(".tl-now");
  var dataEl = document.getElementById("tl-data");
  if (!stops.length || !("IntersectionObserver" in window)) return;
  document.documentElement.classList.add("tl-js");

  var wide = window.matchMedia("(min-width: 1000px)");
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var cur = -1, prev = -1, changedAt = 0;   // page order: 0 is the newest series

  /* ---- which series is current ---- */
  function setCur(i) {
    if (i === cur) return;
    prev = cur; cur = i; changedAt = performance.now();
    stops.forEach(function (s, k) { s.classList.toggle("on", wide.matches && k === cur); });
    if (now) {
      now.firstChild.textContent = cur < 0 ? "" : stops[cur].getAttribute("data-title");
      now.lastChild.textContent = cur < 0 ? now.getAttribute("data-idle") : stops[cur].getAttribute("data-meta");
    }
    kick();
  }
  var io = new IntersectionObserver(function (entries) {
    var next = cur;
    entries.forEach(function (e) {
      var i = stops.indexOf(e.target);
      if (e.isIntersecting) next = i;
      else if (i === 0 && e.boundingClientRect.top > window.innerHeight / 2) next = -1;
    });
    setCur(next);
  }, { rootMargin: "-48% 0px -48% 0px" });
  stops.forEach(function (s) { io.observe(s); });
  window.addEventListener("scroll", function () {   // the last series may never reach the middle of the screen
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4) setCur(stops.length - 1);
  }, { passive: true });

  /* ---- the globe ---- */
  var box = document.querySelector(".globe"), cv = box && box.querySelector("canvas");
  if (!dataEl || !cv || !cv.getContext) return;
  var data = JSON.parse(dataEl.textContent);
  var ctx = cv.getContext("2d");
  var D2R = Math.PI / 180;

  // land points as unit vectors (x east, y north, z towards the viewer at longitude 0)
  var bits = atob(data.land), N = data.n, G = Math.PI * (3 - Math.sqrt(5)), land = [];
  for (var i = 0; i < N; i++) {
    if (!(bits.charCodeAt(i >> 3) & (0x80 >> (i & 7)))) continue;
    var y = 1 - (i + 0.5) * 2 / N, r = Math.sqrt(1 - y * y), a = i * G;
    var lat = Math.asin(y), lon = Math.atan2(Math.sin(a) * r, Math.cos(a) * r);
    land.push(Math.cos(lat) * Math.sin(lon), Math.sin(lat), Math.cos(lat) * Math.cos(lon));
  }
  land = new Float32Array(land);
  function vec(lat, lon) {
    lat *= D2R; lon *= D2R;
    return [Math.cos(lat) * Math.sin(lon), Math.sin(lat), Math.cos(lat) * Math.cos(lon)];
  }

  // stops in page order (newest first); each place as a vector; arcs between consecutive places, older to newer
  var S = data.stops.map(function (s, k) {
    return { k: k, no: s.no, n: s.n, at: s.at.map(function (p) { return vec(p[0], p[1]); }), ll: s.at[0] || null };
  });
  var located = S.filter(function (s) { return s.at.length; });
  function dot3(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }

  // spots: series within about 2.5 degrees of each other share one anchor
  var spots = [];
  located.forEach(function (s) {
    var v = s.at[0], sp = null;
    for (var q = 0; q < spots.length && !sp; q++) if (dot3(spots[q].first, v) > Math.cos(0.045)) sp = spots[q];
    if (!sp) { sp = { first: v, m: [] }; spots.push(sp); }
    sp.m.push(s); s.spot = sp;
  });
  spots.forEach(function (sp) {
    var x = 0, y = 0, z = 0;
    sp.m.forEach(function (s) { x += s.at[0][0]; y += s.at[0][1]; z += s.at[0][2]; });
    var l = Math.hypot(x, y, z); sp.v = [x / l, y / l, z / l];
    sp.m.sort(function (a, b) { return a.no - b.no; });
    sp.m.forEach(function (s, q) { s.slot = q; });
    sp.p = [0, 0, 0, false];
  });

  // legs of the journey, from each series to the next one in time: between spots along the globe, within a spot
  // from pin to pin
  var arcs = [];
  for (var j = 0; j + 1 < located.length; j++) {
    var from = located[j + 1], to = located[j];
    if (from.spot === to.spot) { arcs.push({ pin: true, from: from, to: to.k }); continue; }
    var A = from.spot.v, B = to.spot.v, w = Math.acos(Math.max(-1, Math.min(1, dot3(A, B))));
    arcs.push({ a: A, b: B, w: w, to: to.k });
  }
  var labels = data.labels.map(function (l) {
    var L = { t: l[0], v: vec(l[1], l[2]), side: l[3], spot: null };
    spots.forEach(function (sp) { if (dot3(sp.v, L.v) > Math.cos(0.07)) L.spot = sp; });
    return L;
  });

  // view: the point (lat0, lon0) faces the reader
  var lon0 = (S[0].ll ? S[0].ll[1] : 110) * D2R, lat0 = 22 * D2R, cl, sl, ct, st;
  var size = 0, dpr = 1, R = 0, cx = 0, cy = 0, hits = [], Z = 1;   // Z: zoom, eased in where spots crowd together
  function setView() { cl = Math.cos(lon0); sl = Math.sin(lon0); ct = Math.cos(lat0); st = Math.sin(lat0); }
  function proj(v, alt, out) {          // -> [screen x, screen y, depth (z), outside the disc?]
    var x1 = v[0] * cl - v[2] * sl, z1 = v[0] * sl + v[2] * cl;
    var y2 = v[1] * ct - z1 * st, z2 = v[1] * st + z1 * ct;
    out[0] = cx + x1 * R * Z * alt; out[1] = cy - y2 * R * Z * alt; out[2] = z2;
    out[3] = (x1 * x1 + y2 * y2) * alt * alt > 1;
    return out;
  }
  function resize() {
    var s = box.clientWidth;
    if (!s) return;
    dpr = Math.min(2, window.devicePixelRatio || 1);
    size = s; cv.width = Math.round(s * dpr); cv.height = Math.round(s * dpr);
    R = s * dpr * 0.41; cx = cy = s * dpr / 2;
  }

  var ACC = "219,79,61", HOT = "255,140,112", bins = [], NB = 8;
  for (var b = 0; b < NB; b++) bins.push([]);
  var tmp = [0, 0, 0, false], tmp2 = [0, 0, 0, false];

  function arcPoint(arc, t, out) {      // along the great circle, lifted in the middle
    var w = arc.w, s0 = Math.sin(w), f1 = Math.sin((1 - t) * w) / s0, f2 = Math.sin(t * w) / s0;
    var v = [f1 * arc.a[0] + f2 * arc.b[0], f1 * arc.a[1] + f2 * arc.b[1], f1 * arc.a[2] + f2 * arc.b[2]];
    return proj(v, 1 + (0.025 + 0.09 * Math.min(w, 1.2) / Math.PI) * Math.sin(Math.PI * t), out);   // long arcs stay low, so they slip over the horizon instead of standing up from it
  }
  function fan(sp) {                     // the direction a spot's pins fan out in: away from the spots near it
    var ax = 0, ay = 0;
    for (var q = 0; q < spots.length; q++) {
      var o = spots[q];
      if (o === sp || o.p[2] < 0.04 || dot3(o.v, sp.v) < Math.cos(0.45)) continue;
      var dx = sp.p[0] - o.p[0], dy = sp.p[1] - o.p[1], l = Math.hypot(dx, dy) || 1;
      ax += dx / l / l; ay += dy / l / l;
    }
    sp.dir = ax || ay ? Math.atan2(ay, ax) : -Math.PI / 2;
  }
  function ring(m) { return (18 + 3.5 * m) * dpr; }
  function pinXY(s) {                    // where a series' pin sits on screen, around its spot's anchor
    var sp = s.spot, m = sp.m.length;
    if (m === 1) return [sp.p[0], sp.p[1]];
    var span = Math.min(2 * Math.PI * (m - 1) / m, (m - 1) * 0.78), a = sp.dir - span / 2 + span * s.slot / (m - 1);
    return [sp.p[0] + ring(m) * Math.cos(a), sp.p[1] + ring(m) * Math.sin(a)];
  }
  function strokePin(arc, upto, head) {  // a leg within one spot: a short straight line from pin to pin
    var a = pinXY(arc.from), b = pinXY(S[arc.to]), fade = Math.min(1, arc.from.spot.p[2] * 5);
    if (arc.from.spot.p[2] < 0.04) return;
    var x = a[0] + (b[0] - a[0]) * upto, y = a[1] + (b[1] - a[1]) * upto;
    for (var pass = 0; pass < 2; pass++) {
      ctx.lineWidth = (pass ? 1.6 : 5) * dpr;
      ctx.strokeStyle = pass ? "rgba(" + HOT + "," + (0.95 * fade).toFixed(2) + ")" : "rgba(" + ACC + "," + (0.22 * fade).toFixed(2) + ")";
      ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(x, y); ctx.stroke();
    }
  }
  function strokeArc(arc, upto, head) {
    if (arc.pin) return strokePin(arc, upto, head);
    var steps = Math.max(12, Math.round(56 * arc.w)), pts = [];
    for (var k = 0; k <= steps; k++) {
      var t = k / steps * upto, p = arcPoint(arc, t, [0, 0, 0, false]);
      pts.push(p);
    }
    // in front of the globe: full strength; above its edge but behind it: faint; behind the disc: hidden
    var state = pts.map(function (p) { return p[2] > 0 ? 2 : p[3] ? 1 : 0; });
    for (var want = 1; want <= 2; want++) {
      var dim = want === 2 ? 1 : 0.28;
      for (var pass = 0; pass < 2; pass++) {
        ctx.lineWidth = (pass ? 1.6 : 5) * dpr;
        ctx.strokeStyle = pass ? "rgba(" + HOT + "," + (0.95 * dim).toFixed(2) + ")" : "rgba(" + ACC + "," + (0.22 * dim).toFixed(2) + ")";
        ctx.beginPath();
        for (k = 1; k < pts.length; k++) {
          if (Math.min(state[k - 1], state[k]) !== want && !(want === 2 && state[k - 1] === 2 && state[k] === 2)) continue;
          ctx.moveTo(pts[k - 1][0], pts[k - 1][1]); ctx.lineTo(pts[k][0], pts[k][1]);
        }
        ctx.stroke();
      }
    }
    if (head) {
      var h = pts[pts.length - 1];
      if (h[2] > 0 || h[3]) {
        var g = ctx.createRadialGradient(h[0], h[1], 0, h[0], h[1], 14 * dpr);
        g.addColorStop(0, "rgba(255,240,230,.95)"); g.addColorStop(.25, "rgba(" + HOT + ",.7)"); g.addColorStop(1, "rgba(" + ACC + ",0)");
        ctx.fillStyle = g; ctx.beginPath(); ctx.arc(h[0], h[1], 14 * dpr, 0, 7); ctx.fill();
      }
    }
  }

  function draw(time) {
    var c = ctx, W = cv.width, RZ = R * Z;
    c.clearRect(0, 0, W, W);
    // atmosphere and the body of the globe
    var g = c.createRadialGradient(cx, cy, RZ * 0.92, cx, cy, RZ * 1.22);
    g.addColorStop(0, "rgba(170,180,200,.20)"); g.addColorStop(.3, "rgba(170,180,200,.06)"); g.addColorStop(1, "rgba(170,180,200,0)");
    c.fillStyle = g; c.beginPath(); c.arc(cx, cy, RZ * 1.22, 0, 7); c.fill();
    g = c.createRadialGradient(cx - RZ * .38, cy - RZ * .42, RZ * .05, cx, cy, RZ);
    g.addColorStop(0, "#1b1c1f"); g.addColorStop(1, "#050506");
    c.fillStyle = g; c.beginPath(); c.arc(cx, cy, RZ, 0, 7); c.fill();

    // land: dots get brighter towards the middle of the disc
    for (var b = 0; b < NB; b++) bins[b].length = 0;
    var x1, z1, y2, z2;
    for (var i = 0; i < land.length; i += 3) {
      x1 = land[i] * cl - land[i + 2] * sl; z1 = land[i] * sl + land[i + 2] * cl;
      z2 = land[i + 1] * st + z1 * ct;
      if (z2 <= 0.02) continue;
      y2 = land[i + 1] * ct - z1 * st;
      var sx = cx + x1 * RZ, sy = cy - y2 * RZ;
      if (sx < -4 || sy < -4 || sx > W + 4 || sy > W + 4) continue;
      bins[Math.min(NB - 1, (z2 * NB) | 0)].push(sx, sy);
    }
    var d = Math.max(1.2, 1.55 * dpr * Math.min(1.25, size / 480) * Math.sqrt(Z)), h = d / 2;
    for (b = 0; b < NB; b++) {
      var arr = bins[b];
      if (!arr.length) continue;
      c.fillStyle = "rgba(232,232,236," + (0.1 + 0.8 * Math.pow((b + 0.5) / NB, 0.85)).toFixed(3) + ")";
      c.beginPath();
      for (var k = 0; k < arr.length; k += 2) c.rect(arr[k] - h, arr[k + 1] - h, d, d);
      c.fill();
    }
    c.lineWidth = dpr; c.strokeStyle = "rgba(255,255,255,.07)";
    c.beginPath(); c.arc(cx, cy, RZ, 0, 7); c.stroke();

    for (i = 0; i < spots.length; i++) proj(spots[i].v, 1, spots[i].p);
    for (i = 0; i < spots.length; i++) if (spots[i].m.length > 1) fan(spots[i]);

    // the journey up to the current series: every leg that ends at it or before it (page index >= cur)
    var follow = wide.matches && cur >= 0;
    var grow = reduce ? 1 : Math.min(1, (time - changedAt) / 1100);
    grow = 1 - Math.pow(1 - grow, 3);
    var forward = prev < 0 || cur < prev, moving = grow < 1 && Math.abs(cur - prev) <= 2;
    for (i = 0; i < arcs.length; i++) {
      var A = arcs[i];
      if (!follow || A.to > cur) strokeArc(A, 1, false);
      else if (A.to === cur) strokeArc(A, forward && moving ? grow : 1, forward && moving);   // arriving here
      else if (A.to === prev && !forward && moving) strokeArc(A, 1 - grow, true);              // pulling back
    }

    // spots and their numbered pins
    hits.length = 0;
    var fs = Math.round(10.5 * dpr);
    c.textAlign = "center"; c.textBaseline = "middle";
    for (i = 0; i < spots.length; i++) {
      var sp = spots[i], p = sp.p;
      if (p[2] < 0.04) continue;
      var fade = Math.min(1, p[2] * 5), many = sp.m.length > 1;
      if (many) {                         // the anchor, with a thin line out to each pin
        c.lineWidth = dpr; c.strokeStyle = "rgba(255,255,255," + (0.28 * fade).toFixed(3) + ")";
        c.beginPath();
        sp.m.forEach(function (s) { var q = pinXY(s); c.moveTo(p[0], p[1]); c.lineTo(q[0], q[1]); });
        c.stroke();
        c.fillStyle = "rgba(" + HOT + "," + fade + ")"; c.beginPath(); c.arc(p[0], p[1], 2.4 * dpr, 0, 7); c.fill();
      }
      for (var q = 0; q < sp.m.length; q++) {
        var s = sp.m[q], xy = pinXY(s), seen = !follow || s.k >= cur, on = follow && s.k === cur;
        var rad = (on ? 11 : 8.5) * dpr;
        hits.push([xy[0], xy[1], s.k]);
        if (seen) {
          g = c.createRadialGradient(xy[0], xy[1], 0, xy[0], xy[1], rad * 2.6);
          g.addColorStop(0, "rgba(" + ACC + "," + ((on ? 0.6 : 0.35) * fade).toFixed(3) + ")"); g.addColorStop(1, "rgba(" + ACC + ",0)");
          c.fillStyle = g; c.beginPath(); c.arc(xy[0], xy[1], rad * 2.6, 0, 7); c.fill();
        }
        c.fillStyle = on ? "rgba(255,236,228," + fade + ")" : seen ? "rgba(" + ACC + "," + fade + ")" : "rgba(12,12,14," + (0.85 * fade).toFixed(3) + ")";
        c.beginPath(); c.arc(xy[0], xy[1], rad, 0, 7); c.fill();
        c.lineWidth = dpr; c.strokeStyle = seen ? "rgba(" + HOT + "," + fade + ")" : "rgba(255,255,255," + (0.55 * fade).toFixed(3) + ")";
        c.stroke();
        c.font = "700 " + (on ? Math.round(12 * dpr) : fs) + "px 'Open Sans', system-ui, sans-serif";
        c.fillStyle = on ? "rgba(40,14,10," + fade + ")" : "rgba(255,255,255," + (seen ? fade : 0.8 * fade).toFixed(3) + ")";
        c.fillText(String(s.no), xy[0], xy[1] + 0.5 * dpr);
        if (on && !reduce) {
          var ph = ((time - changedAt) % 1700) / 1700;
          c.lineWidth = 1.4 * dpr; c.strokeStyle = "rgba(" + HOT + "," + ((1 - ph) * 0.9 * fade).toFixed(3) + ")";
          c.beginPath(); c.arc(xy[0], xy[1], rad + ph * 16 * dpr, 0, 7); c.stroke();
        }
      }
    }

    // names of the places facing the reader
    var here = follow && cur >= 0 && S[cur].at.length ? S[cur].spot.v : null;
    c.font = "600 " + Math.round(12 * dpr) + "px 'Open Sans', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif";
    c.textAlign = "left";
    c.textBaseline = "middle";
    c.shadowColor = "rgba(0,0,0,.95)"; c.shadowBlur = 6 * dpr;
    for (i = 0; i < labels.length; i++) {
      var L = labels[i], sp = L.spot, lp = proj(sp ? sp.v : L.v, 1, tmp2);
      if (lp[2] < 0.18) continue;
      var near = here && dot3(here, L.v) > Math.cos(0.07);
      var al = Math.min(1, (lp[2] - 0.18) * 3) * (near ? 1 : 0.7);
      c.fillStyle = near ? "rgba(255,255,255," + al + ")" : "rgba(214,214,218," + al + ")";
      var tw = c.measureText(L.t).width, x, y;
      if (sp && sp.m.length > 1) {        // beyond the pins, in the direction they fan out
        var ux = Math.cos(sp.dir), uy = Math.sin(sp.dir), r0 = ring(sp.m.length) + 14 * dpr;
        x = lp[0] + ux * r0; y = lp[1] + uy * r0;
        c.textAlign = ux > 0.35 ? "left" : ux < -0.35 ? "right" : "center";
        y += uy > 0.35 ? 4 * dpr : uy < -0.35 ? -4 * dpr : 0;
      } else {
        var left = L.side === "left", off = 16 * dpr;
        if (left && lp[0] - off - tw < 4 * dpr) left = false;          // keep the name inside the picture
        else if (!left && lp[0] + off + tw > W - 4 * dpr) left = true;
        c.textAlign = left ? "right" : "left"; x = lp[0] + (left ? -off : off); y = lp[1];
      }
      var x0 = c.textAlign === "right" ? x - tw : c.textAlign === "center" ? x - tw / 2 : x;   // keep it inside
      if (x0 < 4 * dpr) x += 4 * dpr - x0; else if (x0 + tw > W - 4 * dpr) x -= x0 + tw - (W - 4 * dpr);
      c.fillText(L.t, x, y);
    }
    c.shadowBlur = 0;
    if (Z > 1.01) {
      c.globalCompositeOperation = "destination-in";
      g = c.createRadialGradient(cx, cy, W * 0.36, cx, cy, W * 0.5);
      g.addColorStop(0, "rgba(0,0,0,1)"); g.addColorStop(1, "rgba(0,0,0," + Math.max(0, 1 - (Z - 1) * 4).toFixed(3) + ")");
      c.fillStyle = g; c.fillRect(0, 0, W, W);
      c.globalCompositeOperation = "source-over";
    }
  }

  // turning: follow the current place on wide screens, otherwise drift slowly
  var running = false, onScreen = true, last = 0;
  function frame(time) {
    var dt = Math.min(0.05, last ? (time - last) / 1000 : 0.016); last = time;
    var target = null;
    if (wide.matches && cur >= 0) {        // a series with no place (Subway) keeps the last place before it
      for (var k = cur; k < S.length && !target; k++) if (S[k].ll) target = S[k].ll;
    }
    // zoom: in close where series crowd together (several at one spot, or spots near each other), so the pins read
    // clearly while moving among them; out again while the globe turns a long way, then in on arrival
    var zt = 1, tl = target ? target[1] * D2R : 0, tt = target ? Math.max(-0.2, Math.min(0.62, target[0] * D2R * 0.9)) : 0;
    if (target && wide.matches && cur >= 0) {
      var here = null;
      for (k = cur; k < S.length && !here; k++) if (S[k].spot) here = S[k].spot;
      if (here) {
        var crowd = here.m.length >= 3 ? 2.7 : here.m.length === 2 ? 2.1 : 1;
        for (var q = 0; q < spots.length; q++) if (spots[q] !== here && dot3(spots[q].v, here.v) > Math.cos(0.3)) crowd = Math.max(crowd, 2.1);
        if (crowd > 1) tt = Math.max(-0.2, Math.min(0.7, target[0] * D2R));   // centred exactly when zoomed in
        var away = Math.acos(Math.max(-1, Math.min(1, Math.cos(lat0) * Math.cos(tt) * Math.cos(tl - lon0) + Math.sin(lat0) * Math.sin(tt))));
        zt = 1 + (crowd - 1) * Math.exp(-away * 6);
      }
    }
    Z += (zt - Z) * (reduce ? 1 : 1 - Math.exp(-dt * 3));
    if (target) {
      var dl = Math.atan2(Math.sin(tl - lon0), Math.cos(tl - lon0));
      var e = reduce ? 1 : 1 - Math.exp(-dt * 3.2);
      lon0 += dl * e; lat0 += (tt - lat0) * e;
    } else if (!reduce) {
      lon0 += dt * 0.13; lat0 += (0.38 - lat0) * (1 - Math.exp(-dt * 1.5));
    }
    setView();
    draw(time);
    var busy = !reduce || Math.abs(zt - Z) > 0.002 || (target && Math.abs(Math.atan2(Math.sin(target[1] * D2R - lon0), Math.cos(target[1] * D2R - lon0))) > 0.001);
    if (onScreen && !document.hidden && busy) requestAnimationFrame(frame);
    else running = false;
  }
  function kick() {
    if (!running && onScreen && !document.hidden && size) { running = true; last = 0; requestAnimationFrame(frame); }
  }
  new IntersectionObserver(function (e) { onScreen = e[0].isIntersecting; kick(); }).observe(box);
  document.addEventListener("visibilitychange", kick);
  if (wide.addEventListener) wide.addEventListener("change", function () { resize(); setCur(cur); kick(); });
  window.addEventListener("resize", function () { resize(); kick(); });

  // a place on the globe leads to its series
  function nearest(ev) {
    var r = cv.getBoundingClientRect(), x = (ev.clientX - r.left) * dpr, y = (ev.clientY - r.top) * dpr, best = null, bd = 12 * dpr;
    for (var k = 0; k < hits.length; k++) {
      var dd = Math.hypot(hits[k][0] - x, hits[k][1] - y);
      if (dd < bd) { bd = dd; best = hits[k][2]; }
    }
    return best;
  }
  cv.addEventListener("click", function (ev) {
    var k = nearest(ev);
    if (k !== null) stops[k].scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "center" });
  });
  cv.addEventListener("mousemove", function (ev) { cv.style.cursor = nearest(ev) !== null ? "pointer" : ""; });

  resize(); setView(); kick();
})();
