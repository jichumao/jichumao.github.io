/* The home page opening: a Cornell box, path traced live in the browser (WebGL2).

   Each frame traces one more sample per pixel and averages it into the image, so the picture starts as noise and
   converges. Scene: the classic box (red and green walls, a warm area light in the ceiling, a tall white block) open
   towards the viewer, standing on a polished black floor; inside, a glass sphere and a small gold sphere.
   Light: next-event estimation on the area light for the matte surfaces, sampled reflection and refraction for
   glass and metal (caustics included), Russian roulette after three bounces, a thin lens for a little depth of field.

   Dragging sideways turns the box. Rendering stops once the image has converged, while the opening is off screen,
   and in hidden tabs. Without WebGL2 and float render targets, or with "reduce motion", the still picture under the
   canvas (rendered by this same code) is all there is.

   Cornell.make(canvas, options) is also used offline (tools/README) to render that still picture. */
(function () {
  var VS = "#version 300 es\nin vec2 p;void main(){gl_Position=vec4(p,0.,1.);}";

  var TRACE = [
    "#version 300 es",
    "precision highp float; precision highp int;",
    "uniform vec2 uRes; uniform int uFrame; uniform sampler2D uPrev;",
    "uniform vec3 uEye, uFwd, uRight, uUp; uniform float uTanY, uAspect, uFocus, uLens; uniform vec2 uShift;",
    "out vec4 oColor;",
    "#define PI 3.14159265",
    "const float EPS = 2e-4;",
    "const float WT = 0.05;                 // wall thickness",
    "const float LH = 0.995, LS = 0.27;     // ceiling light: height, half size",
    "const vec3 LE = vec3(17.0, 12.6, 8.2); // its emission (warm)",
    "const float GY = -1.0505;              // the floor the box stands on",
    "const vec3 GLASS_C = vec3(-0.40, -0.62, 0.22); const float GLASS_R = 0.38;",
    "const vec3 GOLD_C = vec3(0.56, -0.83, 0.50); const float GOLD_R = 0.17;",
    "const vec3 TALL_C = vec3(0.36, -0.36, -0.32); const vec3 TALL_H = vec3(0.26, 0.64, 0.26); const float TALL_A = 0.36;",
    "uint rs;",
    "uint hash(uint x){ x ^= x >> 16; x *= 0x7feb352du; x ^= x >> 15; x *= 0x846ca68bu; x ^= x >> 16; return x; }",
    "float rnd(){ rs = rs * 747796405u + 2891336453u; uint w = ((rs >> ((rs >> 28u) + 4u)) ^ rs) * 277803737u; w = (w >> 22u) ^ w; return float(w) * (1.0 / 4294967296.0); }",
    // materials
    "const int WHITE = 0, RED = 1, GREEN = 2, OUTSIDE = 3, LIGHT = 4, GLASS = 5, MIRROR = 6, GOLD = 7, FLOOR = 8;",
    "bool slab(vec3 ro, vec3 rd, vec3 lo, vec3 hi, float tmax, inout float t, inout vec3 n) {",
    "  vec3 inv = 1.0 / rd, a = (lo - ro) * inv, b = (hi - ro) * inv, mn = min(a, b), mx = max(a, b);",
    "  float tn = max(max(mn.x, mn.y), mn.z), tf = min(min(mx.x, mx.y), mx.z);",
    "  if (tn > tf || tn < EPS || tn >= min(t, tmax)) return false;",
    "  t = tn; n = tn == mn.x ? vec3(-sign(rd.x), 0., 0.) : tn == mn.y ? vec3(0., -sign(rd.y), 0.) : vec3(0., 0., -sign(rd.z));",
    "  return true;",
    "}",
    "bool ball(vec3 ro, vec3 rd, vec3 c, float r, float tmax, inout float t, inout vec3 n, inout bool inside) {",
    "  vec3 oc = ro - c; float b = dot(oc, rd), q = dot(oc, oc) - r * r, h = b * b - q;",
    "  if (h < 0.) return false; h = sqrt(h);",
    "  float s = -b - h; bool ins = false;",
    "  if (s < EPS) { s = -b + h; ins = true; }",
    "  if (s < EPS || s >= min(t, tmax)) return false;",
    "  t = s; n = (ro + rd * s - c) / r; inside = ins; if (ins) n = -n;",
    "  return true;",
    "}",
    // nearest hit; m = material, n faces the ray
    "bool trace(vec3 ro, vec3 rd, float tmax, out float t, out vec3 n, out int m, out bool inside) {",
    "  t = 1e9; m = -1; inside = false; vec3 nn; float o = 1. + WT;",
    "  if (slab(ro, rd, vec3(-o, -o, -o), vec3(o, -1., 1.), tmax, t, n)) m = n.y > .5 ? WHITE : OUTSIDE;",
    "  if (slab(ro, rd, vec3(-o, 1., -o), vec3(o, o, 1.), tmax, t, n)) m = n.y < -.5 ? WHITE : OUTSIDE;",
    "  if (slab(ro, rd, vec3(-o, -o, -o), vec3(o, o, -1.), tmax, t, n)) m = n.z > .5 ? WHITE : OUTSIDE;",
    "  if (slab(ro, rd, vec3(-o, -o, -o), vec3(-1., o, 1.), tmax, t, n)) m = n.x > .5 ? RED : OUTSIDE;",
    "  if (slab(ro, rd, vec3(1., -o, -o), vec3(o, o, 1.), tmax, t, n)) m = n.x < -.5 ? GREEN : OUTSIDE;",
    // the mirror block, turned about its vertical axis
    "  float ca = cos(TALL_A), sa = sin(TALL_A);",
    "  vec3 lo = ro - TALL_C; lo = vec3(ca * lo.x - sa * lo.z, lo.y, sa * lo.x + ca * lo.z);",
    "  vec3 ld = vec3(ca * rd.x - sa * rd.z, rd.y, sa * rd.x + ca * rd.z);",
    "  if (slab(lo, ld, -TALL_H, TALL_H, tmax, t, nn)) { n = vec3(ca * nn.x + sa * nn.z, nn.y, -sa * nn.x + ca * nn.z); m = WHITE; }",
    "  bool ins = false;",
    "  if (ball(ro, rd, GLASS_C, GLASS_R, tmax, t, n, ins)) { m = GLASS; inside = ins; }",
    "  if (ball(ro, rd, GOLD_C, GOLD_R, tmax, t, n, ins)) { m = GOLD; inside = false; }",
    "  if (rd.y > 0.) { float s = (LH - ro.y) / rd.y; vec3 p = ro + rd * s;",
    "    if (s > EPS && s < min(t, tmax) && abs(p.x) < LS && abs(p.z) < LS) { t = s; n = vec3(0., -1., 0.); m = LIGHT; } }",
    "  if (rd.y < 0.) { float s = (GY - ro.y) / rd.y;",
    "    if (s > EPS && s < min(t, tmax)) { t = s; n = vec3(0., 1., 0.); m = FLOOR; } }",
    "  return m >= 0;",
    "}",
    "bool blocked(vec3 ro, vec3 rd, float dist) { float t; vec3 n; int m; bool i; return trace(ro, rd, dist, t, n, m, i) && m != LIGHT; }",
    "vec3 cosdir(vec3 n) {",
    "  float a = 2. * PI * rnd(), r2 = rnd(), r = sqrt(r2);",
    "  vec3 u = normalize(cross(abs(n.x) > .5 ? vec3(0., 1., 0.) : vec3(1., 0., 0.), n)), v = cross(n, u);",
    "  return normalize(u * cos(a) * r + v * sin(a) * r + n * sqrt(1. - r2));",
    "}",
    "vec3 sphdir() { float z = rnd() * 2. - 1., a = 2. * PI * rnd(), r = sqrt(1. - z * z); return vec3(r * cos(a), r * sin(a), z); }",
    // light from the ceiling panel reaching a matte point, by sampling the panel
    "vec3 direct(vec3 p, vec3 n, vec3 albedo) {",
    "  vec3 lp = vec3((rnd() * 2. - 1.) * LS, LH, (rnd() * 2. - 1.) * LS), d = lp - p;",
    "  float d2 = dot(d, d), dist = sqrt(d2); d /= dist;",
    "  float cs = dot(n, d), cl = d.y;",
    "  if (cs <= 0. || cl <= 0. || blocked(p + n * 1e-3, d, dist - 2e-3)) return vec3(0.);",
    "  return LE * albedo / PI * cs * cl * (4. * LS * LS) / d2;",
    "}",
    "vec3 radiance(vec3 ro, vec3 rd) {",
    "  vec3 L = vec3(0.), T = vec3(1.); bool spec = true, matte = false;",
    "  for (int b = 0; b < 8; b++) {",
    "    float t; vec3 n; int m; bool inside;",
    "    if (!trace(ro, rd, 1e9, t, n, m, inside)) break;",
    "    vec3 p = ro + rd * t;",
    "    if (m == LIGHT) { if (spec) { vec3 e = T * LE; float l = dot(e, vec3(.2126, .7152, .0722)); L += matte && l > 2.5 ? e * (2.5 / l) : e; } break; }   // caustics: clamped, or they sparkle for a long time",
    "    if (m <= OUTSIDE) {",
    "      vec3 al = m == WHITE ? vec3(.73, .71, .68) : m == RED ? vec3(.64, .055, .045) : m == GREEN ? vec3(.12, .46, .09) : vec3(.035);",
    "      L += T * direct(p, n, al); T *= al; rd = cosdir(n); ro = p + n * 1e-3; spec = false; matte = true;",
    "    } else if (m == FLOOR) {",
    "      float c = max(0., -dot(rd, n)), F = .04 + .96 * pow(1. - c, 5.);",
    "      if (rnd() < F) { rd = normalize(reflect(rd, n) + .05 * sphdir()); if (dot(rd, n) <= 0.) rd = reflect(rd, n); spec = true; }",
    "      else { vec3 al = vec3(.012); L += T * direct(p, n, al); T *= al; rd = cosdir(n); spec = false; matte = true; }",
    "      ro = p + n * 1e-3;",
    "    } else if (m == GLASS) {",
    "      float eta = inside ? 1.5 : 1. / 1.5, c = -dot(rd, n); vec3 tr = refract(rd, n, eta);",
    "      float r0 = .04, F = dot(tr, tr) < .5 ? 1. : r0 + (1. - r0) * pow(1. - (inside ? -dot(tr, n) : c), 5.);",
    "      if (rnd() < F) { rd = reflect(rd, n); ro = p + n * 1e-3; } else { rd = tr; ro = p - n * 1e-3; if (!inside) T *= vec3(.97, .99, 1.); }",
    "      spec = true;",
    "    } else {",
    "      vec3 f0 = m == GOLD ? vec3(1., .77, .34) : vec3(.91, .92, .93); float rough = m == GOLD ? .16 : .2;",
    "      vec3 r = reflect(rd, n); rd = normalize(r + rough * sphdir()); if (dot(rd, n) <= 0.) rd = r;",
    "      T *= f0 + (1. - f0) * pow(1. - max(0., dot(rd, n)), 5.); ro = p + n * 1e-3; spec = true;",
    "    }",
    "    if (b > 2) { float q = clamp(max(T.x, max(T.y, T.z)), .05, .95); if (rnd() > q) break; T /= q; }",
    "  }",
    "  return L;",
    "}",
    "void main() {",
    "  uvec2 px = uvec2(gl_FragCoord.xy);",
    "  rs = hash(px.x ^ hash(px.y ^ hash(uint(uFrame) * 2654435761u)));",
    "  vec2 ndc = (gl_FragCoord.xy + vec2(rnd(), rnd()) - .5) / uRes * 2. - 1. - uShift;",
    "  vec3 dir = normalize(uFwd + uRight * ndc.x * uTanY * uAspect + uUp * ndc.y * uTanY);",
    "  vec3 focus = uEye + dir * (uFocus / dot(dir, uFwd));",
    "  float a = 2. * PI * rnd(), r = uLens * sqrt(rnd());",
    "  vec3 eye = uEye + (uRight * cos(a) + uUp * sin(a)) * r;",
    "  vec3 c = radiance(eye, normalize(focus - eye));",
    "  float lum = dot(c, vec3(.2126, .7152, .0722)); if (lum > 8.) c *= 8. / lum;   // tame fireflies",
    "  vec3 prev = uFrame == 0 ? vec3(0.) : texelFetch(uPrev, ivec2(px), 0).rgb;",
    "  oColor = vec4(mix(prev, c, 1. / float(uFrame + 1)), 1.);",
    "}"
  ].join("\n");

  var SHOW = [
    "#version 300 es",
    "precision highp float;",
    "uniform sampler2D uAcc; uniform vec2 uRes; uniform float uFade;",
    "out vec4 o;",
    "void main() {",
    "  ivec2 xy = ivec2(gl_FragCoord.xy), mx = ivec2(uRes) - 1;",
    "  vec3 c = texelFetch(uAcc, xy, 0).rgb * 1.05, g = vec3(0.);",
    "  float r = min(uRes.x, uRes.y) * .02;",
    "  for (int i = 0; i < 64; i++) {                           // a soft glow around the brightest parts: the same",
    "    float f = sqrt((float(i) + .5) / 64.), a = float(i) * 2.39996;   // spiral of taps for every pixel, so it is smooth",
    "    vec3 s = texelFetch(uAcc, clamp(xy + ivec2(vec2(cos(a), sin(a)) * r * f), ivec2(0), mx), 0).rgb;",
    "    g += max(s - 1.2, 0.) * (1. - f);",
    "  }",
    "  c += g * .016;",
    "  c = clamp((c * (2.51 * c + .03)) / (c * (2.43 * c + .59) + .14), 0., 1.);      // ACES",
    "  c = pow(c, vec3(1. / 2.2));",
    "  vec2 q = gl_FragCoord.xy / uRes;",
    "  float n = fract(sin(dot(gl_FragCoord.xy, vec2(12.9898, 78.233))) * 43758.5453);",
    "  o = vec4((c + (n - .5) / 255.) * uFade, 1.);",
    "}"
  ].join("\n");

  function shader(gl, type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  }
  function program(gl, fs) {
    var p = gl.createProgram();
    gl.attachShader(p, shader(gl, gl.VERTEX_SHADER, VS));
    gl.attachShader(p, shader(gl, gl.FRAGMENT_SHADER, fs));
    gl.bindAttribLocation(p, 0, "p");
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    var u = {}, n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
    for (var i = 0; i < n; i++) { var a = gl.getActiveUniform(p, i); u[a.name] = gl.getUniformLocation(p, a.name); }
    return { p: p, u: u };
  }

  /* make(canvas, {preserve}) -> renderer, or null when this browser cannot do it */
  function make(canvas, opt) {
    opt = opt || {};
    var gl = canvas.getContext("webgl2", { antialias: false, depth: false, alpha: false, powerPreference: "high-performance", preserveDrawingBuffer: !!opt.preserve });
    if (!gl || !gl.getExtension("EXT_color_buffer_float")) return null;
    var tr, sh;
    try { tr = program(gl, TRACE); sh = program(gl, SHOW); } catch (e) { return null; }
    var buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    var tex = [], fbo = [], w = 0, h = 0, frame = 0, cur = 0;
    var view = { yaw: 0, pitch: 7 * Math.PI / 180 };

    function size(W, H) {
      if (W === w && H === h) return;
      w = W; h = H; canvas.width = w; canvas.height = h;
      for (var i = 0; i < 2; i++) {
        if (tex[i]) { gl.deleteTexture(tex[i]); gl.deleteFramebuffer(fbo[i]); }
        tex[i] = gl.createTexture();
        gl.bindTexture(gl.TEXTURE_2D, tex[i]);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA32F, w, h, 0, gl.RGBA, gl.FLOAT, null);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
        gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
        fbo[i] = gl.createFramebuffer();
        gl.bindFramebuffer(gl.FRAMEBUFFER, fbo[i]);
        gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex[i], 0);
      }
      frame = 0;
    }

    // framing: on wide pictures the box stands right of centre, leaving room for the name; on tall ones, near the top
    function camera() {
      var aspect = w / h, tanY = Math.tan(19 * Math.PI / 180), wide = aspect > 1.15;
      var shift = wide ? [Math.min(0.42, 0.18 + 0.2 * (aspect - 1.15)), -0.03] : [0, 0.22];
      var dist = wide ? Math.max(2.1 / (2 * 0.6 * tanY), 2.1 / (2 * 0.44 * tanY * aspect))
                      : Math.max(2.1 / (2 * 0.8 * tanY * aspect), 2.1 / (2 * 0.44 * tanY));
      var target = [0, -0.12, 0], cy = Math.cos(view.yaw), sy = Math.sin(view.yaw), cp = Math.cos(view.pitch), sp = Math.sin(view.pitch);
      var eye = [target[0] + dist * sy * cp, target[1] + dist * sp, target[2] + dist * cy * cp];
      var f = norm([target[0] - eye[0], target[1] - eye[1], target[2] - eye[2]]);
      var r = norm([-f[2], 0, f[0]]), u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]];
      return { eye: eye, f: f, r: r, u: u, tanY: tanY, aspect: aspect, shift: shift, focus: dist - 0.15, lens: 0.035 };
    }
    function norm(v) { var l = Math.hypot(v[0], v[1], v[2]); return [v[0] / l, v[1] / l, v[2] / l]; }

    function step(fade) {
      var c = camera(), u = tr.u;
      gl.useProgram(tr.p);
      gl.bindFramebuffer(gl.FRAMEBUFFER, fbo[1 - cur]);
      gl.viewport(0, 0, w, h);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex[cur]);
      gl.uniform1i(u.uPrev, 0); gl.uniform2f(u.uRes, w, h); gl.uniform1i(u.uFrame, frame);
      gl.uniform3fv(u.uEye, c.eye); gl.uniform3fv(u.uFwd, c.f); gl.uniform3fv(u.uRight, c.r); gl.uniform3fv(u.uUp, c.u);
      gl.uniform1f(u.uTanY, c.tanY); gl.uniform1f(u.uAspect, c.aspect); gl.uniform2fv(u.uShift, c.shift);
      gl.uniform1f(u.uFocus, c.focus); gl.uniform1f(u.uLens, c.lens);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      cur = 1 - cur; frame++;
      gl.useProgram(sh.p);
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      gl.viewport(0, 0, w, h);
      gl.bindTexture(gl.TEXTURE_2D, tex[cur]);
      gl.uniform1i(sh.u.uAcc, 0); gl.uniform2f(sh.u.uRes, w, h); gl.uniform1f(sh.u.uFade, fade == null ? 1 : fade);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    }
    return {
      size: size, step: step, gl: gl,
      get frame() { return frame; },
      turn: function (yaw) { view.yaw = yaw; frame = 0; },
      get yaw() { return view.yaw; }
    };
  }
  window.Cornell = { make: make };

  /* ---- on the home page ---- */
  var media = document.querySelector(".hero-pt .hero-media"), canvas = media && media.querySelector(".hero-live");
  if (!canvas) return;
  function still() {                                  // the picture rendered offline by this same code
    var pic = media.querySelector(".hero-still");
    if (!pic) return;
    Array.prototype.forEach.call(pic.querySelectorAll("[data-srcset]"), function (el) {
      el.srcset = el.getAttribute("data-srcset"); el.removeAttribute("data-srcset");
    });
    pic.hidden = false; media.classList.remove("live"); canvas.style.display = "none";
  }
  if (!window.matchMedia || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return still();
  var R = make(canvas);
  if (!R) return still();
  canvas.addEventListener("webglcontextlost", function (e) { e.preventDefault(); onScreen = false; still(); });
  var spp = media.querySelector(".spp"), DONE = 1024, scale = 1, slow = 0, times = [], onScreen = true, running = false, startedAt = 0;

  function fit() {
    var box = media.getBoundingClientRect(), dpr = Math.min(window.devicePixelRatio || 1, 2);
    var k = Math.min(1, Math.sqrt(1.5e6 / (box.width * box.height * dpr * dpr))) * scale;   // at most ~1.5 million pixels
    R.size(Math.max(2, Math.round(box.width * dpr * k)), Math.max(2, Math.round(box.height * dpr * k)));
  }
  function label() {
    if (spp) spp.textContent = R.frame.toLocaleString("en-US") + (R.frame === 1 ? " sample" : " samples") + " per pixel.";
  }
  var last = 0;
  function frame(t) {
    if (!onScreen || document.hidden) { running = false; return; }
    if (last) {                                       // too slow for this screen: trace fewer pixels
      times.push(t - last);
      if (times.length === 24) {
        times.sort(function (a, b) { return a - b; });
        if (times[12] > 45 && slow < 3) { slow++; scale *= 0.72; fit(); }
        times = [];
      }
    }
    last = t;
    if (!startedAt) { startedAt = t; media.classList.add("live"); }
    R.step(Math.min(1, (t - startedAt) / 500));
    if ((R.frame & 7) === 1 || R.frame >= DONE) label();
    if (R.frame >= DONE) { running = false; media.classList.add("done"); return; }
    requestAnimationFrame(frame);
  }
  function go() {
    if (running || !onScreen || document.hidden || R.frame >= DONE) return;
    running = true; last = 0; times = []; requestAnimationFrame(frame);
  }
  fit();
  window.addEventListener("resize", function () { fit(); go(); });
  document.addEventListener("visibilitychange", go);
  if ("IntersectionObserver" in window) new IntersectionObserver(function (e) { onScreen = e[0].isIntersecting; go(); }).observe(media);

  // dragging sideways turns the box (vertical drags still scroll the page on touch screens)
  var down = null;
  canvas.addEventListener("pointerdown", function (e) { down = { x: e.clientX, yaw: R.yaw }; canvas.setPointerCapture(e.pointerId); media.classList.add("dragging"); });
  canvas.addEventListener("pointermove", function (e) {
    if (!down) return;
    var yaw = Math.max(-0.6, Math.min(0.6, down.yaw - (e.clientX - down.x) / 420));
    if (yaw !== R.yaw) { R.turn(yaw); media.classList.remove("done"); go(); }
  });
  function up() { down = null; media.classList.remove("dragging"); }
  canvas.addEventListener("pointerup", up); canvas.addEventListener("pointercancel", up);
  go();
})();
