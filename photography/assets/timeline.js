/* The timeline page.
   The list runs newest first. Beside it (on wide screens) a dotted globe turns to the series in the middle of the
   screen: the places already passed are lit, an arc is drawn from each to the next, and the current one pulses.
   On narrow screens the globe sits above the list, turns slowly and shows every place.
   The globe's land is a Fibonacci lattice of points; which of them are land comes in #tl-data (tools/footprint.py). */
(function () {
  var stops = Array.prototype.slice.call(document.querySelectorAll(".stop"));
  var now = document.querySelector(".tl-now");
  var dataEl = document.getElementById("tl-data");
  if (!stops.length || !("IntersectionObserver" in window)) return;
  document.documentElement.classList.add("tl-js");

  var wide = window.matchMedia("(min-width: 1000px)");
  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var cur = -1, changedAt = 0;

  /* ---- which series is current ---- */
  function setCur(i) {
    if (i === cur) return;
    cur = i; changedAt = performance.now();
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

  // stops in page order; each place as a vector; arcs between consecutive places
  var S = data.stops.map(function (s, k) {
    return { k: k, n: s.n, at: s.at.map(function (p) { return vec(p[0], p[1]); }), ll: s.at[0] || null };
  });
  var located = S.filter(function (s) { return s.at.length; });
  var arcs = [];
  for (var j = 0; j + 1 < located.length; j++) {
    var A = located[j].at[0], B = located[j + 1].at[0];
    var w = Math.acos(Math.max(-1, Math.min(1, A[0] * B[0] + A[1] * B[1] + A[2] * B[2])));
    if (w > 0.02) arcs.push({ a: A, b: B, w: w, to: located[j + 1].k });
  }
  var labels = data.labels.map(function (l) { return { t: l[0], v: vec(l[1], l[2]), side: l[3] }; });

  // view: the point (lat0, lon0) faces the reader
  var lon0 = (S[0].ll ? S[0].ll[1] : 110) * D2R, lat0 = 22 * D2R, cl, sl, ct, st;
  var size = 0, dpr = 1, R = 0, cx = 0, cy = 0, hits = [];
  function setView() { cl = Math.cos(lon0); sl = Math.sin(lon0); ct = Math.cos(lat0); st = Math.sin(lat0); }
  function proj(v, alt, out) {          // -> [screen x, screen y, depth (z), outside the disc?]
    var x1 = v[0] * cl - v[2] * sl, z1 = v[0] * sl + v[2] * cl;
    var y2 = v[1] * ct - z1 * st, z2 = v[1] * st + z1 * ct;
    out[0] = cx + x1 * R * alt; out[1] = cy - y2 * R * alt; out[2] = z2;
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
  function strokeArc(arc, upto, head) {
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
    var c = ctx, W = cv.width;
    c.clearRect(0, 0, W, W);
    // atmosphere and the body of the globe
    var g = c.createRadialGradient(cx, cy, R * 0.92, cx, cy, R * 1.22);
    g.addColorStop(0, "rgba(170,180,200,.20)"); g.addColorStop(.3, "rgba(170,180,200,.06)"); g.addColorStop(1, "rgba(170,180,200,0)");
    c.fillStyle = g; c.beginPath(); c.arc(cx, cy, R * 1.22, 0, 7); c.fill();
    g = c.createRadialGradient(cx - R * .38, cy - R * .42, R * .05, cx, cy, R);
    g.addColorStop(0, "#1b1c1f"); g.addColorStop(1, "#050506");
    c.fillStyle = g; c.beginPath(); c.arc(cx, cy, R, 0, 7); c.fill();

    // land: dots get brighter towards the middle of the disc
    for (var b = 0; b < NB; b++) bins[b].length = 0;
    var x1, z1, y2, z2;
    for (var i = 0; i < land.length; i += 3) {
      x1 = land[i] * cl - land[i + 2] * sl; z1 = land[i] * sl + land[i + 2] * cl;
      z2 = land[i + 1] * st + z1 * ct;
      if (z2 <= 0.02) continue;
      y2 = land[i + 1] * ct - z1 * st;
      bins[Math.min(NB - 1, (z2 * NB) | 0)].push(cx + x1 * R, cy - y2 * R);
    }
    var d = Math.max(1.2, 1.55 * dpr * Math.min(1.25, size / 480)), h = d / 2;
    for (b = 0; b < NB; b++) {
      var arr = bins[b];
      if (!arr.length) continue;
      c.fillStyle = "rgba(232,232,236," + (0.1 + 0.8 * Math.pow((b + 0.5) / NB, 0.85)).toFixed(3) + ")";
      c.beginPath();
      for (var k = 0; k < arr.length; k += 2) c.rect(arr[k] - h, arr[k + 1] - h, d, d);
      c.fill();
    }
    c.lineWidth = dpr; c.strokeStyle = "rgba(255,255,255,.07)";
    c.beginPath(); c.arc(cx, cy, R, 0, 7); c.stroke();

    // arcs up to the current series; the newest one draws itself in
    var follow = wide.matches, upto = follow ? cur : S.length - 1;
    var grow = reduce ? 1 : Math.min(1, (time - changedAt) / 1100);
    grow = 1 - Math.pow(1 - grow, 3);
    for (i = 0; i < arcs.length; i++) {
      var A = arcs[i];
      if (A.to > upto) continue;
      var last = follow && A.to === cur && grow < 1;
      strokeArc(A, last ? grow : 1, last);
    }

    // places
    hits.length = 0;
    for (i = 0; i < S.length; i++) {
      var s = S[i], seen = !follow || i <= cur, on = follow && i === cur;
      for (var q = 0; q < s.at.length; q++) {
        var p = proj(s.at[q], 1, tmp);
        if (p[2] < 0.04) continue;
        var fade = Math.min(1, p[2] * 5), rad = (2.2 + 0.6 * Math.sqrt(s.n)) * dpr;
        hits.push([p[0], p[1], s.k]);
        if (seen) {
          g = c.createRadialGradient(p[0], p[1], 0, p[0], p[1], rad * 4);
          g.addColorStop(0, "rgba(" + ACC + "," + (0.45 * fade).toFixed(3) + ")"); g.addColorStop(1, "rgba(" + ACC + ",0)");
          c.fillStyle = g; c.beginPath(); c.arc(p[0], p[1], rad * 4, 0, 7); c.fill();
          c.fillStyle = on ? "rgba(255,236,228," + fade + ")" : "rgba(" + HOT + "," + fade + ")";
          c.beginPath(); c.arc(p[0], p[1], rad, 0, 7); c.fill();
        } else {
          c.lineWidth = dpr; c.strokeStyle = "rgba(255,255,255," + (0.55 * fade).toFixed(3) + ")";
          c.beginPath(); c.arc(p[0], p[1], rad, 0, 7); c.stroke();
        }
        if (on && !reduce) {
          var ph = ((time - changedAt) % 1700) / 1700;
          c.lineWidth = 1.4 * dpr; c.strokeStyle = "rgba(" + HOT + "," + ((1 - ph) * 0.9 * fade).toFixed(3) + ")";
          c.beginPath(); c.arc(p[0], p[1], rad + ph * 18 * dpr, 0, 7); c.stroke();
        }
      }
    }

    // names of the places facing the reader
    var here = follow && cur >= 0 && S[cur].at.length ? S[cur].at[0] : null;
    c.font = "600 " + Math.round(12 * dpr) + "px 'Open Sans', 'PingFang SC', 'Microsoft YaHei', system-ui, sans-serif";
    c.textBaseline = "middle";
    c.shadowColor = "rgba(0,0,0,.95)"; c.shadowBlur = 6 * dpr;
    for (i = 0; i < labels.length; i++) {
      var L = labels[i], lp = proj(L.v, 1, tmp2);
      if (lp[2] < 0.18) continue;
      var near = here && (here[0] * L.v[0] + here[1] * L.v[1] + here[2] * L.v[2]) > 0.9994;
      var al = Math.min(1, (lp[2] - 0.18) * 3) * (near ? 1 : 0.7);
      c.fillStyle = near ? "rgba(255,255,255," + al + ")" : "rgba(214,214,218," + al + ")";
      var tw = c.measureText(L.t).width, left = L.side === "left";
      if (left && lp[0] - 11 * dpr - tw < 4 * dpr) left = false;          // keep the name inside the picture
      else if (!left && lp[0] + 11 * dpr + tw > W - 4 * dpr) left = true;
      c.textAlign = left ? "right" : "left";
      c.fillText(L.t, lp[0] + (left ? -11 : 11) * dpr, lp[1]);
    }
    c.shadowBlur = 0;
  }

  // turning: follow the current place on wide screens, otherwise drift slowly
  var running = false, onScreen = true, last = 0;
  function frame(time) {
    var dt = Math.min(0.05, last ? (time - last) / 1000 : 0.016); last = time;
    var target = null;
    if (wide.matches && cur >= 0) {
      for (var k = cur; k >= 0 && !target; k--) if (S[k].ll) target = S[k].ll;
    }
    if (target) {
      var tl = target[1] * D2R, tt = Math.max(-0.2, Math.min(0.62, target[0] * D2R * 0.9));
      var dl = Math.atan2(Math.sin(tl - lon0), Math.cos(tl - lon0));
      var e = reduce ? 1 : 1 - Math.exp(-dt * 3.2);
      lon0 += dl * e; lat0 += (tt - lat0) * e;
    } else if (!reduce) {
      lon0 += dt * 0.13; lat0 += (0.38 - lat0) * (1 - Math.exp(-dt * 1.5));
    }
    setView();
    draw(time);
    var busy = !reduce || (target && Math.abs(Math.atan2(Math.sin(target[1] * D2R - lon0), Math.cos(target[1] * D2R - lon0))) > 0.001);
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
    var r = cv.getBoundingClientRect(), x = (ev.clientX - r.left) * dpr, y = (ev.clientY - r.top) * dpr, best = null, bd = 16 * dpr;
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
