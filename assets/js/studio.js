/* The home page opening: the site's name, JICHU · ART, path traced live in the browser (WebGL2, no libraries).

   Every letter is a different material, warm on the left and cool on the right: J crystal (dispersive), I chrome,
   C gold, H neon tubes (a light), U a milky material light travels through (subsurface scattering), the dot a
   glowing sphere (a light), A sapphire glass (absorbing), R titanium under a thin oxide film (interference colours),
   T porcelain. They stand on a wet black floor in light haze, lit by the H, the dot, a large softbox above and
   behind the camera and a cool strip above and behind the letters.

   Rendering, per pixel and frame: one camera path through a thin lens, averaged into the image so the picture
   starts as noise and converges.
   - Surfaces: GGX microfacet reflection with Smith shadowing and Schlick Fresnel (coloured for the metals), clear
     coats over matte bases, glass with Fresnel reflection and refraction.
   - Lights: the H's tubes, the dot and the softbox, each sampled over its surface by next-event estimation;
     light sampling and BSDF sampling are combined with multiple importance sampling (power heuristic). A dim
     studio around the set (a strip behind the camera, a glow far behind the letters) is found by BSDF rays only.
   - Spectral: a path that reaches the crystal or the titanium picks a wavelength and is weighted by its colour
     (CIE 1931). The crystal's index of refraction follows Cauchy's law, so it splits light into colours; the film's
     reflectance comes from the interference of light reflected at its two faces (Airy's formula), and its thickness
     changes up the letter, so the colours do too. The sapphire absorbs by Beer-Lambert along the path inside.
   - Participating media: homogeneous haze with free-flight distance sampling and a Henyey-Greenstein phase
     function. Light scattered towards the camera is estimated on every camera ray at a point drawn along it
     (proportionally to transmittance), and at each scattering event further along the path.
   - Geometry: each letter a signed distance field (strokes extruded, edges rounded; the H's tubes are capsules),
     ray-marched inside its bounding box; the floor and the softbox analytic.
   - Subsurface scattering (the U): a random walk inside the letter, with Fresnel at its surface.
   - Light linking: the strip behind the letters lights them but is left out of the floor's reflections.
   - Denoising: an edge-aware a-trous wavelet filter (as in SVGF), four passes, guided by first-hit normals and
     distances and by each pixel's own noise estimate (from its samples' spread), so it lets go as the average
     converges; after 600 samples the average is shown as it is.
   - Display: ACES tone mapping, a soft glow around bright light, a slight vignette.

   Dragging sideways turns the camera. Rendering stops once the image has converged (1,024 samples), while the
   opening is off screen and in hidden tabs, and traces fewer pixels when frames come slowly. Without WebGL2 and
   float render targets, or with "reduce motion", the still picture (rendered by this same code) is shown instead.

   Studio.make(canvas, {preserve}) -> renderer is also how the still pictures were made (see the README). */
(function () {
  var VS = "#version 300 es\nin vec2 p;void main(){gl_Position=vec4(p,0.,1.);}";

  var TRACE = [
    "#version 300 es",
    "precision highp float; precision highp int;",
    "uniform vec2 uRes; uniform int uFrame, uSeed; uniform sampler2D uPrev, uPrevGeo, uPrev1, uPrev2, uPrev3;",
    "uniform vec3 uEye, uFwd, uRight, uUp; uniform float uTanY, uAspect, uFocus, uLens; uniform vec2 uShift;",
    "uniform vec4 uL[9];              // each letter: x, z, cos and sin of its turn about the vertical",
    "uniform vec4 uA; uniform float uWZ;   // the arch of light behind the letters: centre x and z, radius, tube; the wall's z",
    // light transport is linear in what the lights emit, so each group of lights gets its own running average, traced
    // with white light; their colours are mixed in afterwards, every frame, and can change without tracing again
    "layout(location = 0) out vec4 oColor;    // the white lights (softbox, strip, dome); alpha: luminance squared of it all",
    "layout(location = 1) out vec4 oGeo;      // running average of what the camera ray hit first: normal, distance",
    // the arch's colour runs smoothly along it: three colours blended by quadratic Bernstein weights, one group each
    "layout(location = 2) out vec4 oG1;       // the arch's first colour (strongest at its left foot) and the neon H",
    "layout(location = 3) out vec4 oG2;       // its middle colour (strongest at the top) and the dot",
    "layout(location = 4) out vec4 oG3;       // its last colour (at the right foot)",
    "#define PI 3.14159265",
    "const float EPS = 1e-4;",
    // the letters: strokes HW wide either side of their centre lines, cap height 1, extruded 2 * DEPTH, edges rounded
    "const float HW = 0.085, DEPTH = 0.13, RR = 0.028, TUBE = 0.05, LIFT = 0.085;",
    "const vec2 GX[9] = vec2[9](vec2(-.335, .275), vec2(-.085, .085), vec2(-.485, .487), vec2(-.36, .36), vec2(-.385, .385), vec2(-.1, .1), vec2(-.465, .465), vec2(-.385, .405), vec2(-.445, .445));",
    "const int NONE = 0, FLOOR = 1, KEY = 2, RIM = 3, WALL = 4, ARCH = 5, LETTER = 10;   // LETTER + 0..8: J I C H U . A R T",
    // lights: the neon H, the glowing dot, and a large softbox above and behind the camera, turned towards the letters
    // (from there its reflection in the floor falls outside the picture), with a faint dome of light overhead
    "const float NEON_W = 9.5, DOT_W = 7.5, ARCH_W = 7.;            // how bright the coloured lights are, before colour",
    "const float DOT_R = 0.1, DOT_Y = 0.565;",
    "const vec3 KEY_C = vec3(2.5, 9., 14.), KEY_U = vec3(-3.15, 0., .563), KEY_V = vec3(-.197, 1.894, -1.101);   // centre, half-sides",
    "const vec3 KEY_E = vec3(6.2, 6.0, 5.6), SKY = vec3(.018, .02, .026);",
    // a cool strip above and behind the letters, out of the picture, that draws their top and back edges
    "const vec3 RIM_C = vec3(0., 7.6, -3.2), RIM_U = vec3(4.5, 0., 0.), RIM_V = vec3(0., 0.112, 0.224), RIM_E = vec3(3.4, 3.8, 4.5);",
    "const float P_NEON = 0.2, P_DOT = 0.1, P_ARCH = 0.3, P_RIM = 0.1;   // how often each light is sampled (the softbox: the rest)",
    "const float P_KEY = 1. - P_NEON - P_DOT - P_ARCH - P_RIM;",
    "const float NEON_L = 2.62;                                       // total length of the H's tubes",
    "const float SIG = 0.0045, HG = 0.8;                             // haze density, forward scattering",
    "const float SSS_T = 16.; const vec3 SSS_A = vec3(.998, .997, .995);  // inside the U: how often light scatters, what it keeps",
    "const vec3 SAPPHIRE = vec3(.35, .18, .14);                       // the A's absorption per unit length: clear, faintly cool",
    "const vec3 MED_C = vec3(0., 1., 0.); const float MED_R = 24.;",
    "const vec3 WL[31] = vec3[31](vec3(0.009, 0.000, 0.178), vec3(0.090, 0.000, 0.601), vec3(0.209, 0.000, 1.921), vec3(0.304, 0.000, 4.079), vec3(0.457, 0.000, 5.102), vec3(0.297, 0.000, 5.229), vec3(0.000, 0.000, 4.886), vec3(0.000, 0.094, 3.756), vec3(0.000, 0.512, 2.300), vec3(0.000, 1.007, 1.245), vec3(0.000, 1.621, 0.608), vec3(0.000, 2.415, 0.178), vec3(0.000, 3.281, 0.000), vec3(0.000, 3.841, 0.000), vec3(0.000, 3.945, 0.000), vec3(0.000, 3.760, 0.000), vec3(0.732, 3.318, 0.000), vec3(1.779, 2.690, 0.000), vec3(2.798, 1.937, 0.000), vec3(3.640, 1.149, 0.000), vec3(4.170, 0.434, 0.000), vec3(4.213, 0.000, 0.000), vec3(3.737, 0.000, 0.000), vec3(2.937, 0.000, 0.000), vec3(2.055, 0.000, 0.000), vec3(1.283, 0.000, 0.000), vec3(0.714, 0.000, 0.000), vec3(0.354, 0.000, 0.000), vec3(0.156, 0.000, 0.000), vec3(0.060, 0.007, 0.000), vec3(0.020, 0.007, 0.000));",
    "uint rs; float gLam, gFilm; vec3 gN; float gZ;",
    "vec3 L0, L1, L2, L3;                                              // what each group of lights has given this sample",
    "void addW(vec4 w, vec3 v) { L0 += v * w.x; L1 += v * w.y; L2 += v * w.z; L3 += v * w.w; }",
    "vec3 archW(float u) { return vec3((1. - u) * (1. - u), 2. * u * (1. - u), u * u); }",
    "uint hash(uint x){ x ^= x >> 16; x *= 0x7feb352du; x ^= x >> 15; x *= 0x846ca68bu; x ^= x >> 16; return x; }",
    "float rnd(){ rs = rs * 747796405u + 2891336453u; uint w = ((rs >> ((rs >> 28u) + 4u)) ^ rs) * 277803737u; w = (w >> 22u) ^ w; return float(w) * (1.0 / 4294967296.0); }",
    "vec3 specw(float l) { float x = clamp((l - 400.) / 10., 0., 29.999); int i = int(x); return mix(WL[i], WL[i + 1], x - float(i)); }",

    // the letters as signed distance fields, each in its own frame (x right, y up from the floor, z towards the front)
    "float seg(vec2 p, vec2 a, vec2 b) { vec2 pa = p - a, ba = b - a; return length(pa - ba * clamp(dot(pa, ba) / dot(ba, ba), 0., 1.)); }",
    "float seg3(vec3 p, vec3 a, vec3 b) { vec3 pa = p - a, ba = b - a; return length(pa - ba * clamp(dot(pa, ba) / dot(ba, ba), 0., 1.)); }",
    "float arc(vec2 p, vec2 c, float r, float a0, float a1) {         // a circular arc from angle a0 round to a1",
    "  vec2 q = p - c; float a = a0 + mod(atan(q.y, q.x) - a0, 2. * PI);",
    "  if (a <= a1) return abs(length(q) - r);",
    "  return min(length(q - r * vec2(cos(a0), sin(a0))), length(q - r * vec2(cos(a1), sin(a1))));",
    "}",
    "float strokes(int g, vec2 p) {                                   // distance to the centre lines of letter g",
    "  if (g == 0) return min(min(seg(p, vec2(.19, 1.), vec2(.19, .22)), arc(p, vec2(-.03, .22), .22, PI, 2. * PI)), seg(p, vec2(-.25, .22), vec2(-.25, .36)));",
    "  if (g == 1) return seg(p, vec2(0., 0.), vec2(0., 1.));",
    "  if (g == 2) return arc(p, vec2(.06, .5), .46, .73, 5.55);",
    "  if (g == 4) return min(min(seg(p, vec2(-.3, 1.), vec2(-.3, .3)), seg(p, vec2(.3, 1.), vec2(.3, .3))), arc(p, vec2(0., .3), .3, PI, 2. * PI));",
    "  if (g == 6) return min(min(seg(p, vec2(-.38, 0.), vec2(0., 1.)), seg(p, vec2(.38, 0.), vec2(0., 1.))), seg(p, vec2(-.25, .34), vec2(.25, .34)));",
    "  if (g == 7) return min(min(min(seg(p, vec2(-.3, 0.), vec2(-.3, 1.)), seg(p, vec2(-.3, 1.), vec2(.02, 1.))), min(arc(p, vec2(.02, .75), .25, -1.5708, 1.5708), seg(p, vec2(.02, .5), vec2(-.3, .5)))), seg(p, vec2(-.04, .5), vec2(.32, 0.)));",
    "  return min(seg(p, vec2(-.36, 1.), vec2(.36, 1.)), seg(p, vec2(0., 1.), vec2(0., 0.)));",
    "}",
    "float glyph(int g, vec3 p) {",
    "  p.y -= LIFT;",
    "  if (g == 3) return min(min(seg3(p, vec3(-.31, 0., 0.), vec3(-.31, 1., 0.)), seg3(p, vec3(.31, 0., 0.), vec3(.31, 1., 0.))), seg3(p, vec3(-.31, .5, 0.), vec3(.31, .5, 0.))) - TUBE;   // neon tubes",
    "  if (g == 5) return length(p - vec3(0., DOT_Y - LIFT, 0.)) - DOT_R;",
    "  vec2 w = vec2(strokes(g, p.xy) - HW + RR, abs(p.z) - DEPTH + RR);   // extruded, with rounded edges",
    "  return min(max(w.x, w.y), 0.) + length(max(w, 0.)) - RR;",
    "}",
    "vec3 toLocal(vec3 v, vec4 L) { return vec3(L.z * v.x - L.w * v.z, v.y, L.w * v.x + L.z * v.z); }",
    "vec3 toWorld(vec3 v, vec4 L) { return vec3(L.z * v.x + L.w * v.z, v.y, -L.w * v.x + L.z * v.z); }",
    "bool marchLetter(int g, vec3 ro, vec3 rd, float tmax, out float t) {",
    "  vec4 L = uL[g]; vec3 o = toLocal(ro - vec3(L.x, 0., L.y), L), d = toLocal(rd, L);",
    "  vec3 lo = vec3(GX[g].x - .01, -.01, -DEPTH - .01), hi = vec3(GX[g].y + .01, 1. + 2. * LIFT + .01, DEPTH + .01);",
    "  vec3 inv = 1. / (d + vec3(1e-9)), ta = (lo - o) * inv, tb = (hi - o) * inv, tn = min(ta, tb), tx = max(ta, tb);",
    "  float a = max(max(tn.x, tn.y), max(tn.z, EPS * 10.)), b = min(min(tx.x, tx.y), min(tx.z, tmax));",
    "  if (a >= b) return false;",
    "  t = a;",
    "  for (int i = 0; i < 110; i++) {",
    "    float s = abs(glyph(g, o + d * t));                           // abs: rays inside the glass J march out the same way",
    "    if (s < 2e-4) return true;",
    "    t += max(s * .9, 3e-4); if (t > b) return false;",
    "  }",
    "  return false;",
    "}",
    "vec3 letterNormal(int g, vec3 p) {                               // outward, in the world",
    "  vec4 L = uL[g]; vec3 q = toLocal(p - vec3(L.x, 0., L.y), L);",
    "  const vec2 k = vec2(1., -1.) * 4e-4;",
    "  vec3 n = k.xyy * glyph(g, q + k.xyy) + k.yyx * glyph(g, q + k.yyx) + k.yxy * glyph(g, q + k.yxy) + k.xxx * glyph(g, q + k.xxx);",
    "  return normalize(toWorld(n, L));",
    "}",
    "vec2 sphereSpan(vec3 ro, vec3 rd, vec3 c, float r) {",
    "  vec3 oc = ro - c; float b = dot(oc, rd), h = b * b - dot(oc, oc) + r * r;",
    "  if (h < 0.) return vec2(1e9, -1e9); h = sqrt(h); return vec2(-b - h, -b + h);",
    "}",
    // the arch: half a thin torus standing on the floor, facing the camera; marched only through the slab it lies in
    "float archSDF(vec3 p) { return length(vec2(length(p.xy - vec2(uA.x, 0.)) - uA.z, p.z - uA.y)) - uA.w; }",
    "float archU(vec3 p) { return clamp(1. - atan(p.y, p.x - uA.x) / PI, 0., 1.); }   // 0 at the left foot, 1 at the right",
    "vec3 archNormal(vec3 p) { vec3 r = normalize(vec3(p.x - uA.x, p.y, 0.)); return normalize(p - vec3(uA.x, 0., uA.y) - r * uA.z); }",
    "bool archHit(vec3 ro, vec3 rd, float tmax, out float s) {",
    "  s = 0.; if (abs(rd.z) < 1e-5) return false;",
    "  float t0 = (uA.y - 2. * uA.w - ro.z) / rd.z, t1 = (uA.y + 2. * uA.w - ro.z) / rd.z;",
    "  float a = max(min(t0, t1), EPS), b = min(max(t0, t1), tmax); if (a >= b) return false;",
    "  float t = a;",
    "  for (int i = 0; i < 32; i++) {",
    "    vec3 p = ro + rd * t; float d = archSDF(p);",
    "    if (d < 2e-4) { s = t; return p.y > 0.; }",
    "    t += max(d, 2e-4); if (t > b) return false;",
    "  }",
    "  return false;",
    "}",
    "bool rect(vec3 ro, vec3 rd, vec3 C, vec3 U, vec3 V, float tmax, out float s) {   // a rectangle: centre, half-sides",
    "  vec3 n = cross(U, V); float dn = dot(rd, n); s = 0.;",
    "  if (abs(dn) < 1e-9) return false;",
    "  s = dot(C - ro, n) / dn; vec3 q = ro + rd * s - C;",
    "  return s > EPS && s < tmax && abs(dot(q, U)) < dot(U, U) && abs(dot(q, V)) < dot(V, V);",
    "}",
    // nearest surface
    "int trace(vec3 ro, vec3 rd, float tmax, out float t) {",
    "  t = tmax; int m = NONE; float s;",
    "  if (rd.y < 0.) { s = -ro.y / rd.y; if (s > EPS && s < t) { t = s; m = FLOOR; } }",
    "  if (rect(ro, rd, KEY_C, KEY_U, KEY_V, t, s)) { t = s; m = KEY; }",
    "  if (rect(ro, rd, RIM_C, RIM_U, RIM_V, t, s)) { t = s; m = RIM; }",
    "  if (rd.z < 0.) { s = (uWZ - ro.z) / rd.z; if (s > EPS && s < t) { t = s; m = WALL; } }",
    "  if (archHit(ro, rd, t, s)) { t = s; m = ARCH; }",
    "  for (int g = 0; g < 9; g++) if (marchLetter(g, ro, rd, t, s)) { t = s; m = LETTER + g; }",
    "  return m;",
    "}",
    "bool visible(vec3 a, vec3 b) {          // nothing between two points (the glass J counts as opaque here)",
    "  vec3 d = b - a; float l = length(d), t;",
    "  return trace(a, d / l, l - 5e-3, t) == NONE;",
    "}",
    "vec3 ortho(vec3 n) { return normalize(cross(abs(n.x) > .5 ? vec3(0., 1., 0.) : vec3(1., 0., 0.), n)); }",
    "vec3 cosdir(vec3 n) { float a = 2. * PI * rnd(), r2 = rnd(), r = sqrt(r2); vec3 u = ortho(n), v = cross(n, u); return normalize(u * cos(a) * r + v * sin(a) * r + n * sqrt(1. - r2)); }",
    "float D_ggx(float nh, float a) { float a2 = a * a, d = nh * nh * (a2 - 1.) + 1.; return a2 / (PI * d * d); }",
    "float G1(float nv, float a) { float a2 = a * a; return 2. * nv / (nv + sqrt(a2 + (1. - a2) * nv * nv)); }",
    "vec3 schlick(vec3 f0, float c) { return f0 + (1. - f0) * pow(1. - c, 5.); }",
    "vec3 ggxHalf(vec3 n, float a) { float u = rnd(), th = atan(a * sqrt(u / (1. - u))), ph = 2. * PI * rnd(); vec3 t = ortho(n), b = cross(n, t); return normalize(t * cos(ph) * sin(th) + b * sin(ph) * sin(th) + n * cos(th)); }",
    // light sampling: picks a light and a point on it; returns its radiance, fills direction, distance and pdf (solid angle)
    "vec3 sampleLight(vec3 p, bool noRim, out vec3 wi, out float dist, out float pdf, out vec4 gw) {",
    "  vec3 lp, ln, Le; float area, sel, x = rnd(); gw = vec4(1., 0., 0., 0.);",
    "  if (x < P_NEON) {",
    "    vec4 L = uL[3]; float u = rnd() * NEON_L, ph = 2. * PI * rnd(); vec3 a, r;",
    "    if (u < 1.) { a = vec3(-.31, u, 0.); r = vec3(cos(ph), 0., sin(ph)); }",
    "    else if (u < 2.) { a = vec3(.31, u - 1., 0.); r = vec3(cos(ph), 0., sin(ph)); }",
    "    else { a = vec3(-.31 + (u - 2.), .5, 0.); r = vec3(0., cos(ph), sin(ph)); }",
    "    lp = toWorld(a + r * TUBE + vec3(0., LIFT, 0.), L) + vec3(L.x, 0., L.y); ln = toWorld(r, L);",
    "    area = 2. * PI * TUBE * NEON_L; Le = vec3(NEON_W); sel = P_NEON; gw = vec4(0., 1., 0., 0.);",
    "  } else if (x < P_NEON + P_DOT) {",
    "    vec4 L = uL[5]; float z = 2. * rnd() - 1., ph = 2. * PI * rnd(), sn = sqrt(1. - z * z);",
    "    ln = vec3(sn * cos(ph), z, sn * sin(ph)); lp = vec3(L.x, DOT_Y, L.y) + ln * DOT_R;",
    "    area = 4. * PI * DOT_R * DOT_R; Le = vec3(DOT_W); sel = P_DOT; gw = vec4(0., 0., 1., 0.);",
    "  } else if (x < P_NEON + P_DOT + P_ARCH) {",
    "    float u = rnd(), th = PI * (1. - u), ph = 2. * PI * rnd(); vec3 r = vec3(cos(th), sin(th), 0.);",
    "    ln = r * cos(ph) + vec3(0., 0., sin(ph)); lp = vec3(uA.x, 0., uA.y) + r * uA.z + ln * uA.w;",
    "    area = 2. * PI * uA.w * PI * uA.z; Le = vec3(ARCH_W); sel = P_ARCH; gw = vec4(0., archW(u));",
    "  } else if (x < P_NEON + P_DOT + P_ARCH + P_RIM) {",
    "    lp = RIM_C + RIM_U * (rnd() * 2. - 1.) + RIM_V * (rnd() * 2. - 1.); ln = normalize(cross(RIM_U, RIM_V));",
    "    area = 4. * length(RIM_U) * length(RIM_V); Le = noRim ? vec3(0.) : RIM_E; sel = P_RIM;",
    "  } else {",
    "    lp = KEY_C + KEY_U * (rnd() * 2. - 1.) + KEY_V * (rnd() * 2. - 1.); ln = normalize(cross(KEY_U, KEY_V));",
    "    area = 4. * length(KEY_U) * length(KEY_V); Le = KEY_E; sel = P_KEY;",
    "  }",
    "  vec3 d = lp - p; float d2 = dot(d, d); dist = sqrt(d2); wi = d / dist;",
    "  float cl = dot(-wi, ln); if (cl <= 0.) { pdf = 0.; return vec3(0.); }",
    "  pdf = sel * d2 / (cl * area);",
    "  if (!visible(p, lp)) return vec3(0.);",
    "  return Le * exp(-SIG * dist);",
    "}",
    "float lightPdf(int m, vec3 wi, float dist, vec3 ln) {             // pdf of having sampled this point of light m",
    "  float cl = abs(dot(wi, ln)); if (cl < 1e-4) return 0.;",
    "  float a = m == LETTER + 3 ? P_NEON / (2. * PI * TUBE * NEON_L) : m == LETTER + 5 ? P_DOT / (4. * PI * DOT_R * DOT_R)",
    "          : m == ARCH ? P_ARCH / (2. * PI * uA.w * PI * uA.z)",
    "          : m == RIM ? P_RIM / (4. * length(RIM_U) * length(RIM_V)) : P_KEY / (4. * length(KEY_U) * length(KEY_V));",
    "  return a * dist * dist / cl;",
    "}",
    // thin-film interference (the R): a clear oxide film over metal, its reflectance per wavelength (Airy, unpolarised)
    "float film(float ci, float lambda, float d) {",
    "  const float n1 = 2.4, n2 = 4.2; float s = 1. - ci * ci;",
    "  float c1 = sqrt(max(0., 1. - s / (n1 * n1))), c2 = sqrt(max(0., 1. - s / (n2 * n2)));",
    "  float cp = cos(4. * PI * n1 * d * c1 / lambda), R = 0.;",
    "  for (int k = 0; k < 2; k++) {",
    "    float r1 = k == 0 ? (ci - n1 * c1) / (ci + n1 * c1) : (n1 * ci - c1) / (n1 * ci + c1);",
    "    float r2 = k == 0 ? (n1 * c1 - n2 * c2) / (n1 * c1 + n2 * c2) : (n2 * c1 - n1 * c2) / (n2 * c1 + n1 * c2);",
    "    R += (r1 * r1 + r2 * r2 + 2. * r1 * r2 * cp) / (1. + r1 * r1 * r2 * r2 + 2. * r1 * r2 * cp);",
    "  }",
    "  return .5 * R;",
    "}",
    // what a ray finds when it leaves the studio: a dim dome overhead; behind the camera a long soft strip, low down,
    // for the chrome, the gold and the film to mirror; far behind the letters a faint glow near the floor, which the
    // glass bends and the floor reflects
    "vec3 env(vec3 d) {",
    "  float el = asin(clamp(d.y, -1., 1.));",
    "  vec3 c = SKY * max(d.y, 0.);",
    "  if (d.z > 0.) c += vec3(1.05, 1.02, .98) * smoothstep(.5, .12, abs(el - .3)) * smoothstep(1., .6, abs(d.x));",
    "  else c += vec3(.03, .036, .055) * exp(-pow((el - .04) / .12, 2.)) * smoothstep(1., .2, abs(d.x));",
    "  return c;",
    "}",
    // the opaque materials: 0 a clear coat over a matte base, 1 a metal (GGX, coloured Fresnel),
    // 2 a metal under a thin oxide film (its Fresnel term worked out per wavelength)
    "void material(int m, out int kind, out vec3 c, out float a) {",
    "  kind = 0;",
    "  if (m == LETTER + 2) { kind = 1; c = vec3(.91, .92, .93); a = .2; }             // C: brushed silver",
    "  else if (m == LETTER + 7) { c = vec3(.004); a = .012; }                          // R: black glass, a dark mirror",
    "  else if (m == LETTER + 8) { c = vec3(.86, .85, .83); a = .03; }                 // T: glazed porcelain",
    "  else if (m == WALL) { c = vec3(.016, .016, .018); a = .25; }                    // the back wall, far off: dark satin",
    "  else { c = vec3(.018, .018, .02); a = .022; }                                     // the wet black floor",
    "}",
    "vec3 bsdf(int m, vec3 n, vec3 wo, vec3 wi, out float pdf) {",
    "  float nwo = max(1e-4, dot(n, wo)), nwi = dot(n, wi); pdf = 0.;",
    "  if (nwi <= 0.) return vec3(0.);",
    "  int kind; vec3 c; float a; material(m, kind, c, a);",
    "  vec3 h = normalize(wi + wo); float nh = max(0., dot(n, h)), hw = max(1e-4, dot(h, wo)), D = D_ggx(nh, a);",
    "  if (kind > 0) {",
    "    vec3 F = kind == 1 ? schlick(c, hw) : vec3(film(hw, gLam, gFilm));",
    "    pdf = D * nh / (4. * hw); return D * G1(nwo, a) * G1(nwi, a) * F / (4. * nwo * nwi);",
    "  }",
    "  float pc = .04 + .96 * pow(1. - nwo, 5.);",
    "  pdf = pc * D * nh / (4. * hw) + (1. - pc) * nwi / PI;",
    "  return vec3(D * G1(nwo, a) * G1(nwi, a) * (.04 + .96 * pow(1. - hw, 5.)) / (4. * nwo * nwi)) + (1. - pc) * c / PI;",
    "}",
    "vec3 bsdfDir(int m, vec3 n, vec3 wo) {",
    "  int kind; vec3 c; float a; material(m, kind, c, a);",
    "  if (kind > 0) return reflect(-wo, ggxHalf(n, a));",
    "  float pc = .04 + .96 * pow(1. - max(0., dot(n, wo)), 5.);",
    "  return rnd() < pc ? reflect(-wo, ggxHalf(n, a)) : cosdir(n);",
    "}",
    "float hgPhase(float c) { float g2 = HG * HG; return (1. - g2) / (4. * PI * pow(1. + g2 - 2. * HG * c, 1.5)); }",
    "vec3 hgSample(vec3 d) {",
    "  float g2 = HG * HG, s = (1. - g2) / (1. - HG + 2. * HG * rnd()), c = (1. + g2 - s * s) / (2. * HG);",
    "  float sn = sqrt(max(0., 1. - c * c)), ph = 2. * PI * rnd(); vec3 t = ortho(d), b = cross(d, t);",
    "  return normalize(t * cos(ph) * sn + b * sin(ph) * sn + d * c);",
    "}",

    "void radiance(vec3 ro, vec3 rd, float lambda) {",
    "  vec3 T = vec3(1.); L0 = L1 = L2 = L3 = vec3(0.); vec4 gw;",
    "  int mode = 0;                 // how we got here: 0 camera or specular, 1 medium (light already sampled), 2 MIS",
    "  float lastPdf = 0.; bool split = false, fromFloor = false;",
    "  for (int b = 0; b < 8; b++) {",
    "    float t;",
    "    vec2 med = sphereSpan(ro, rd, MED_C, MED_R);",
    "    int m = trace(ro, rd, max(med.y, EPS), t);",
    "    if (b == 0) {                                            // for the denoiser: what this camera ray hit first",
    "      gZ = m == NONE ? 1e3 : t;",
    "      vec3 hp = ro + rd * t;",
    "      vec3 g = m == NONE || m == KEY || m == RIM ? -rd : m == FLOOR ? vec3(0., 1., 0.) : m == WALL ? vec3(0., 0., 1.)",
    "             : m == ARCH ? archNormal(hp) : letterNormal(m - LETTER, hp);",
    "      gN = dot(g, rd) > 0. ? -g : g;",
    "    }",
    // light scattered towards the camera by the haze. On the camera ray it is estimated once per sample, at a point
    // drawn along the whole ray (so every pixel gets some, instead of a few getting a lot); further along the path,
    // where a free flight happens to stop in the haze
    "    float tseg = min(t, med.y), tf = -log(1. - rnd()) / SIG; bool along = b == 0 && tseg > 0.;",
    "    if (along) {",
    "      float a = 1. - exp(-SIG * tseg), ts = -log(1. - rnd() * a) / SIG, dist, pdf; vec3 wi;",
    "      vec3 Le = sampleLight(ro + rd * ts, false, wi, dist, pdf, gw);",
    "      if (pdf > 0.) addW(gw, T * a * Le * hgPhase(dot(rd, wi)) / pdf);",
    "    }",
    "    if (tf < tseg) {                                         // the free flight ends in the haze: scatter",
    "      vec3 p = ro + rd * tf, wi; float dist, pdf;",
    "      if (!along) { vec3 Le = sampleLight(p, false, wi, dist, pdf, gw); if (pdf > 0.) addW(gw, T * Le * hgPhase(dot(rd, wi)) / pdf); }",
    "      ro = p; rd = hgSample(rd); mode = 1; continue;",
    "    }",
    "    if (m == NONE) { if (mode != 1) L0 += T * env(rd); break; }  // found only by BSDF rays, never sampled directly",
    "    vec3 p = ro + rd * t, n = m == FLOOR ? vec3(0., 1., 0.) : m == WALL ? vec3(0., 0., 1.) : m == KEY ? normalize(cross(KEY_U, KEY_V))",
    "         : m == RIM ? normalize(cross(RIM_U, RIM_V)) : m == ARCH ? archNormal(p) : letterNormal(m - LETTER, p);",
    "    bool inside = dot(n, rd) > 0.; if (inside) n = -n;          // n now faces the ray",
    "    if (m == KEY || m == RIM || m == ARCH || m == LETTER + 3 || m == LETTER + 5) {   // a light",
    "      vec3 Le = m == KEY ? KEY_E : m == RIM ? RIM_E : vec3(m == ARCH ? ARCH_W : m == LETTER + 3 ? NEON_W : DOT_W);",
    "      vec4 g = m == ARCH ? vec4(0., archW(archU(p))) : m == LETTER + 3 ? vec4(0., 1., 0., 0.) : m == LETTER + 5 ? vec4(0., 0., 1., 0.) : vec4(1., 0., 0., 0.);",
    "      if ((m == KEY || m == RIM) && inside || m == RIM && fromFloor) break;   // the panels shine one way",
    "      if (mode == 0) addW(g, T * Le);",
    "      else if (mode == 2) { float pl = lightPdf(m, rd, t, n); addW(g, T * Le * lastPdf * lastPdf / (lastPdf * lastPdf + pl * pl)); }",
    "      break;",
    "    }",
    "    vec3 wo = -rd;",
    "    if (m == LETTER + 0) {                                     // J: glass, dispersive",
    "      if (!split) { split = true; T *= specw(lambda); }",
    "      float lu = lambda * 1e-3, ior = 1.47 + .0110 / (lu * lu);",
    "      float eta = inside ? ior : 1. / ior, c = dot(wo, n); vec3 tr = refract(rd, n, eta);",
    "      float r0 = (ior - 1.) / (ior + 1.); r0 *= r0;",
    "      float F = dot(tr, tr) < .5 ? 1. : r0 + (1. - r0) * pow(1. - (inside ? -dot(tr, n) : c), 5.);",
    "      if (rnd() < F) { rd = reflect(rd, n); ro = p + n * 1e-3; } else { rd = tr; ro = p - n * 1e-3; }",
    "      mode = 0;",
    "    } else if (m == LETTER + 1) {                              // I: chrome",
    "      vec3 r = reflect(rd, ggxHalf(n, .02)); if (dot(r, n) <= 0.) r = reflect(rd, n);",
    "      T *= schlick(vec3(.92, .93, .95), max(0., dot(n, wo))); rd = r; ro = p + n * 1e-3; mode = 0;",
    "    } else if (m == LETTER + 6) {                              // A: sapphire glass, its colour absorbed on the way through",
    "      if (inside) T *= exp(-SAPPHIRE * t);                     // Beer-Lambert, over the distance travelled inside",
    "      float ior = 1.62, eta = inside ? ior : 1. / ior, c = dot(wo, n); vec3 tr = refract(rd, n, eta);",
    "      float r0 = (ior - 1.) / (ior + 1.); r0 *= r0;",
    "      float F = dot(tr, tr) < .5 ? 1. : r0 + (1. - r0) * pow(1. - (inside ? -dot(tr, n) : c), 5.);",
    "      if (rnd() < F) { rd = reflect(rd, n); ro = p + n * 1e-3; } else { rd = tr; ro = p - n * 1e-3; }",
    "      mode = 0;",
    "    } else if (m == LETTER + 4) {                              // U: translucent, light wanders inside (random walk)",
    "      float ior = 1.4, r0 = (ior - 1.) / (ior + 1.); r0 *= r0;",
    "      if (rnd() < r0 + (1. - r0) * pow(1. - dot(wo, n), 5.)) { rd = reflect(rd, n); ro = p + n * 1e-3; mode = 0; continue; }",
    "      rd = refract(rd, n, 1. / ior); ro = p - n * 1e-3;",
    "      bool gone = false;",
    "      for (int k = 0; k < 64 && !gone; k++) {",
    "        float d = -log(1. - rnd()) / SSS_T, s;",
    "        if (!marchLetter(4, ro, rd, d, s)) {               // scattered before reaching the surface",
    "          ro += rd * d; T *= SSS_A; float z = 2. * rnd() - 1., ph = 2. * PI * rnd(), sn = sqrt(1. - z * z);",
    "          rd = vec3(sn * cos(ph), z, sn * sin(ph)); continue;",
    "        }",
    "        vec3 q = ro + rd * s, no = letterNormal(4, q), tr = refract(rd, -no, ior);",
    "        float F = dot(tr, tr) < .5 ? 1. : r0 + (1. - r0) * pow(1. - dot(tr, no), 5.);",
    "        if (rnd() < F) { rd = reflect(rd, -no); ro = q - no * 1e-3; } else { rd = tr; ro = q + no * 1e-3; gone = true; }",
    "      }",
    "      if (!gone) break;",
    "      mode = 0;",
    "    } else {                                                   // light sampling and BSDF sampling, combined by MIS",
    "      vec3 q = p + n * 1e-3, wi; float dist, pl, pb;",
    "      vec3 Le = sampleLight(q, m == FLOOR, wi, dist, pl, gw);   // light linking: the strip is not seen in the floor",
    // the far wall is nearly black: light that bounces off it again adds nothing visible, so a path ends there, after
    // the light it receives directly (then without the MIS weight, since no BSDF ray will follow to share it)
    "      bool last = m == WALL;",
    "      if (pl > 0.) { vec3 f = bsdf(m, n, wo, wi, pb); if (pb > 0.) addW(gw, T * Le * f * dot(n, wi) / pl * (last ? 1. : pl * pl / (pl * pl + pb * pb))); }",
    "      if (last) break;",
    "      rd = bsdfDir(m, n, wo);",
    "      vec3 f = bsdf(m, n, wo, rd, pb);",
    "      if (pb <= 0.) break;",
    "      T *= f * dot(n, rd) / pb; lastPdf = pb; mode = 2; ro = q; fromFloor = m == FLOOR;",
    "    }",
    "    if (b > 2) { float q = clamp(max(T.x, max(T.y, T.z)), .05, .95); if (rnd() > q) break; T /= q; }",
    "  }",
    "}",
    "void main() {",
    "  uvec2 px = uvec2(gl_FragCoord.xy);",
    "  rs = hash(px.x ^ hash(px.y ^ hash(uint(uFrame) * 2654435761u ^ uint(uSeed) * 40503u)));",
    "  float lambda = 400. + 300. * fract(float(uFrame) * .618034 + rnd());   // stratified over frames",
    "  vec2 ndc = (gl_FragCoord.xy + vec2(rnd(), rnd()) - .5) / uRes * 2. - 1. - uShift;",
    "  vec3 dir = normalize(uFwd + uRight * ndc.x * uTanY * uAspect + uUp * ndc.y * uTanY);",
    "  vec3 focus = uEye + dir * (uFocus / dot(dir, uFwd));",
    "  float a = 2. * PI * rnd(), r = uLens * sqrt(rnd());",
    "  vec3 eye = uEye + (uRight * cos(a) + uUp * sin(a)) * r;",
    "  radiance(eye, normalize(focus - eye), lambda);",
    "  float lum = dot(L0 + L1 + L2 + L3, vec3(.2126, .7152, .0722));",
    // a sample gone wrong (0/0 at a grazing angle) would stay in the average for good, and the denoiser would spread
    // it into a black square; such a sample is dropped
    "  if (isnan(lum) || isinf(lum) || !(lum >= 0. && lum < 1e8)) { L0 = L1 = L2 = L3 = vec3(0.); lum = 0.; }",
    "  if (lum > 10.) { float s = 10. / lum; L0 *= s; L1 *= s; L2 *= s; L3 *= s; lum = 10.; }   // tame fireflies",
    "  ivec2 ip = ivec2(px); bool z = uFrame == 0;",
    "  float k = 1. / float(uFrame + 1);",
    "  oColor = mix(z ? vec4(0.) : texelFetch(uPrev, ip, 0), vec4(L0, lum * lum), k);",
    "  oGeo = mix(z ? vec4(0.) : texelFetch(uPrevGeo, ip, 0), vec4(gN, gZ), k);",
    "  oG1 = mix(z ? vec4(0.) : texelFetch(uPrev1, ip, 0), vec4(L1, 0.), k);",
    "  oG2 = mix(z ? vec4(0.) : texelFetch(uPrev2, ip, 0), vec4(L2, 0.), k);",
    "  oG3 = mix(z ? vec4(0.) : texelFetch(uPrev3, ip, 0), vec4(L3, 0.), k);",
    "}"
  ].join("\n");

  // where the letters stand: one gently curved row on a wide screen; on a tall one JICHU behind and ·ART in front
  var WIDTH = [0.61, 0.17, 0.97, 0.72, 0.77, 0.2, 0.93, 0.79, 0.89], CENTRE = [-0.03, 0, 0.001, 0, 0, 0, 0, 0.01, 0];
  function arch(wide) {             // the arch behind the letters (centre x, z, radius, tube) and the back wall's z
    return { a: wide ? new Float32Array([0, -3.4, 3.05, 0.032]) : new Float32Array([0, -3.6, 1.6, 0.03]), wall: -7.5 };
  }
  // the colours the lights flow through: amber, coral, rose, violet, indigo, and back again, each group a little behind
  // the one on its left, so the colour travels across the picture
  var FLOW = [[1.0, 0.52, 0.16], [1.0, 0.3, 0.24], [0.92, 0.22, 0.5], [0.56, 0.26, 0.95], [0.22, 0.36, 1.0]];
  function flow(x) {
    var n = FLOW.length - 1, u = x - Math.floor(x / (2 * n)) * 2 * n;
    if (u > n) u = 2 * n - u;
    var i = Math.min(n - 1, Math.floor(u)), f = u - i; f = f * f * (3 - 2 * f);
    var a = FLOW[i], b = FLOW[i + 1], c = [a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f, a[2] + (b[2] - a[2]) * f];
    var l = 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
    return [c[0] * 0.5 / l, c[1] * 0.5 / l, c[2] * 0.5 / l];   // every colour equally bright
  }
  function colours(t) {              // t in seconds; a full sweep there and back takes about 40 s
    var x = t * 0.2;
    return [].concat(flow(x), flow(x - 1.0), flow(x - 2.0));
  }
  function layout(wide) {
    var L = new Float32Array(36), rows = wide ? [[0, 1, 2, 3, 4, 5, 6, 7, 8]] : [[0, 1, 2, 3, 4], [5, 6, 7, 8]];
    var zs = wide ? [0] : [-1.45, 1.35], GAP = 0.17, K = wide ? 0.055 : 0.03;
    rows.forEach(function (row, ri) {
      var total = row.reduce(function (s, g) { return s + WIDTH[g]; }, 0) + GAP * (row.length - 1), x = -total / 2;
      row.forEach(function (g) {
        var cx = x + WIDTH[g] / 2 - CENTRE[g], yaw = Math.atan(2 * K * cx);   // on a shallow curve, each letter facing its middle
        L[g * 4] = cx; L[g * 4 + 1] = zs[ri] - K * cx * cx; L[g * 4 + 2] = Math.cos(yaw); L[g * 4 + 3] = Math.sin(yaw);
        x += WIDTH[g] + GAP;
      });
    });
    return L;
  }

  var COMBINE = [                   // the groups of lights, each in its colour of the moment
    "#version 300 es",
    "precision highp float;",
    "uniform sampler2D uS, uG1, uG2, uG3; uniform vec3 uC1, uC2, uC3;",
    "out vec4 o;",
    "void main() {",
    "  ivec2 p = ivec2(gl_FragCoord.xy);",
    "  vec4 s = texelFetch(uS, p, 0); vec3 g1 = texelFetch(uG1, p, 0).rgb, g2 = texelFetch(uG2, p, 0).rgb, g3 = texelFetch(uG3, p, 0).rgb;",
    "  float l = dot(s.rgb + g1 + g2 + g3, vec3(.2126, .7152, .0722));",
    "  vec4 c = vec4(s.rgb + uC1 * g1 + uC2 * g2 + uC3 * g3, max(0., s.a - l * l));   // alpha: how much the samples vary",
    "  if (any(isnan(c)) || any(isinf(c))) c = vec4(0.);             // never hand the denoiser a broken pixel",
    "  c = max(c, vec4(0.));",
    "  o = c;",
    "}"
  ].join("\n");

  var DENOISE = [
    "#version 300 es",
    "precision highp float;",
    "uniform sampler2D uCol, uGeo; uniform int uStep, uFirst; uniform float uN; uniform vec2 uRes;",
    "out vec4 o;",
    "float lumi(vec3 c) { return dot(c, vec3(.2126, .7152, .0722)); }",
    "float comp(float l) { l = max(l, 0.); return l / (1. + l); }  // compressed, so the lights do not dominate",
    "void main() {",
    "  ivec2 p = ivec2(gl_FragCoord.xy), mx = ivec2(uRes) - 1;",
    "  vec4 c0 = texelFetch(uCol, p, 0), g0 = texelFetch(uGeo, p, 0); vec3 n0 = g0.xyz / max(length(g0.xyz), 1e-4);",
    "  float lp = comp(lumi(c0.rgb)), sig;",
    "  if (uFirst == 1) {                     // how noisy this pixel's average is: from its samples once there are a few,",
    "    float l = lumi(c0.rgb), s1 = 0., s2 = 0., va = 0.;       // before that from its neighbours",
    "    for (int y = -1; y <= 1; y++) for (int x = -1; x <= 1; x++) { vec4 t = texelFetch(uCol, clamp(p + ivec2(x, y), ivec2(0), mx), 0); float q = comp(lumi(t.rgb)); s1 += q; s2 += q * q; va += t.a; }",
    "    s1 /= 9.;",
    // the variance is averaged over the 3 x 3 neighbourhood (as in SVGF): a pixel whose few samples all missed the
    // light looks certain on its own, and would otherwise stay as a dark speck
    "    sig = uN >= 6. ? sqrt(max(c0.a, va / 9.) / uN) / ((1. + l) * (1. + l)) : sqrt(max(0., s2 / 9. - s1 * s1));",
    "  } else sig = c0.a;",
    "  const float K[3] = float[3](.375, .25, .0625);",
    "  vec3 acc = vec3(0.); float ws = 0.;",
    "  for (int y = -2; y <= 2; y++) for (int x = -2; x <= 2; x++) {",
    "    ivec2 q = clamp(p + ivec2(x, y) * uStep, ivec2(0), mx);",
    "    vec4 c = texelFetch(uCol, q, 0), g = texelFetch(uGeo, q, 0);",
    "    float w = K[abs(x)] * K[abs(y)]",
    "      * pow(max(0., dot(n0, g.xyz / max(length(g.xyz), 1e-4))), 32.)",
    "      * exp(-abs(g0.w - g.w) / (.012 * g0.w * float(uStep) + 1e-3))",
    "      * exp(-abs(lp - comp(lumi(c.rgb))) / (4. * sig + 1e-4));",
    "    acc += c.rgb * w; ws += w;",
    "  }",
    "  o = vec4(acc / max(ws, 1e-6), sig * .6);                    // each pass leaves less noise for the next",
    "}"
  ].join("\n");

  var SHOW = [
    "#version 300 es",
    "precision highp float;",
    "uniform sampler2D uAcc; uniform vec2 uRes; uniform float uFade, uExposure;",
    "out vec4 o;",
    "void main() {",
    "  ivec2 xy = ivec2(gl_FragCoord.xy), mx = ivec2(uRes) - 1;",
    "  vec3 c = texelFetch(uAcc, xy, 0).rgb * uExposure, g = vec3(0.);",
    "  float r = min(uRes.x, uRes.y) * .025;",
    "  for (int i = 0; i < 64; i++) {                           // a soft glow around the brightest light: the same",
    "    float f = sqrt((float(i) + .5) / 64.), a = float(i) * 2.39996;   // spiral of taps for every pixel, so it is smooth",
    "    vec3 s = texelFetch(uAcc, clamp(xy + ivec2(vec2(cos(a), sin(a)) * r * f), ivec2(0), mx), 0).rgb * uExposure;",
    "    g += max(s - 1., 0.) * (1. - f);",
    "  }",
    "  c += g * .03;",
    "  vec2 q = gl_FragCoord.xy / uRes - .5;",
    "  c *= 1. - .35 * dot(q, q);                                // vignette",
    "  c = clamp((c * (2.51 * c + .03)) / (c * (2.43 * c + .59) + .14), 0., 1.);   // ACES",
    "  c = pow(c, vec3(1. / 2.2));",
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
    for (var i = 0; i < n; i++) { var a = gl.getActiveUniform(p, i); u[a.name.replace(/\[0\]$/, "")] = gl.getUniformLocation(p, a.name); }
    return { p: p, u: u };
  }

  function make(canvas, opt) {
    opt = opt || {};
    var gl = canvas.getContext("webgl2", { antialias: false, depth: false, alpha: false, powerPreference: "high-performance", preserveDrawingBuffer: !!opt.preserve });
    if (!gl || !gl.getExtension("EXT_color_buffer_float")) return null;
    if (gl.getParameter(gl.MAX_DRAW_BUFFERS) < 5) return null;
    var tr, dn, sh, cb;
    try { tr = program(gl, TRACE); dn = program(gl, DENOISE); sh = program(gl, SHOW); cb = program(gl, COMBINE); } catch (e) { if (opt.log) opt.log(String(e)); return null; }
    var buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    var tex = [], geo = [], grp = [[], [], []], fbo = [], dtex = [], dfbo = [], ctex = null, cfbo = null, w = 0, h = 0, frame = 0, cur = 0;
    var time = opt.time == null ? 1.3 : opt.time, bar = null;
    // GPU time per frame from timer queries, where the browser offers them: read a few frames later, without waiting
    var tq = gl.getExtension("EXT_disjoint_timer_query_webgl2"), pending = [], gpu = [], gen = 0;
    var DENOISE_UNTIL = 1e9;          // always: its weights follow each pixel's remaining noise, so it fades out by itself
    var view = { yaw: 0, pitch: 7 * Math.PI / 180 };

    function texture(fmt) {
      var t = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texImage2D(gl.TEXTURE_2D, 0, fmt, w, h, 0, gl.RGBA, fmt === gl.RGBA32F ? gl.FLOAT : gl.HALF_FLOAT, null);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
      return t;
    }
    function size(W, H) {
      if (W === w && H === h) return;
      w = W; h = H; canvas.width = w; canvas.height = h; gen++; gpu = [];
      var A = [gl.COLOR_ATTACHMENT0, gl.COLOR_ATTACHMENT1, gl.COLOR_ATTACHMENT2, gl.COLOR_ATTACHMENT3, gl.COLOR_ATTACHMENT4];
      for (var i = 0; i < 2; i++) {
        if (tex[i]) {
          [tex[i], geo[i], dtex[i], grp[0][i], grp[1][i], grp[2][i]].forEach(function (t) { gl.deleteTexture(t); });
          gl.deleteFramebuffer(fbo[i]); gl.deleteFramebuffer(dfbo[i]);
        }
        tex[i] = texture(gl.RGBA32F); geo[i] = texture(gl.RGBA16F); dtex[i] = texture(gl.RGBA16F);
        for (var g = 0; g < 3; g++) grp[g][i] = texture(gl.RGBA32F);
        fbo[i] = gl.createFramebuffer();
        gl.bindFramebuffer(gl.FRAMEBUFFER, fbo[i]);
        [tex[i], geo[i], grp[0][i], grp[1][i], grp[2][i]].forEach(function (t, k) { gl.framebufferTexture2D(gl.FRAMEBUFFER, A[k], gl.TEXTURE_2D, t, 0); });
        gl.drawBuffers(A);
        dfbo[i] = gl.createFramebuffer();
        gl.bindFramebuffer(gl.FRAMEBUFFER, dfbo[i]);
        gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, dtex[i], 0);
      }
      if (ctex) { gl.deleteTexture(ctex); gl.deleteFramebuffer(cfbo); }
      ctex = texture(gl.RGBA16F); cfbo = gl.createFramebuffer();
      gl.bindFramebuffer(gl.FRAMEBUFFER, cfbo);
      gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, ctex, 0);
      frame = 0;
    }
    // framing: the row across a wide picture, a little above the middle; on a tall one both rows, seen from higher up
    var lay = null, layWide = null;
    function camera() {
      var aspect = w / h, tanY = Math.tan(17 * Math.PI / 180), wide = aspect > 1.15;
      if (layWide !== wide) { layWide = wide; lay = layout(wide); bar = arch(wide); }
      var target = wide ? [0, 0.62, -0.35] : [0, 0.62, 0];
      var dist = wide ? Math.max(7.4, 4.75 / (tanY * aspect)) : Math.max(7.5, 2.12 / (tanY * aspect));
      var shift = wide ? [0, 0.12] : [0, 0.26], pitch = view.pitch + (wide ? 0 : 0.53);
      var cy = Math.cos(view.yaw), sy = Math.sin(view.yaw), cp = Math.cos(pitch), sp = Math.sin(pitch);
      var eye = [target[0] + dist * sy * cp, target[1] + dist * sp, target[2] + dist * cy * cp];
      var f = norm([target[0] - eye[0], target[1] - eye[1], target[2] - eye[2]]);
      var r = norm([-f[2], 0, f[0]]), u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]];
      var gc = [-eye[0], 0.62 - eye[1], -eye[2]];             // in focus: the middle of the letters
      return { eye: eye, f: f, r: r, u: u, tanY: tanY, aspect: aspect, shift: shift, focus: gc[0] * f[0] + gc[1] * f[1] + gc[2] * f[2], lens: wide ? 0.03 : 0.012 };
    }
    function norm(v) { var l = Math.hypot(v[0], v[1], v[2]); return [v[0] / l, v[1] / l, v[2] / l]; }

    function step(fade, n) {          // n samples per pixel (default 1), then shown once
      var c = camera(), u = tr.u, q = null;
      n = Math.max(1, n | 0);
      if (tq && pending.length < 6) { q = gl.createQuery(); gl.beginQuery(tq.TIME_ELAPSED_EXT, q); }
      gl.useProgram(tr.p);
      gl.bindFramebuffer(gl.FRAMEBUFFER, fbo[1 - cur]);
      gl.viewport(0, 0, w, h);
      [tex[cur], geo[cur], grp[0][cur], grp[1][cur], grp[2][cur]].forEach(function (t, k) { gl.activeTexture(gl.TEXTURE0 + k); gl.bindTexture(gl.TEXTURE_2D, t); });
      gl.uniform1i(u.uPrev, 0); gl.uniform1i(u.uPrevGeo, 1); gl.uniform1i(u.uPrev1, 2); gl.uniform1i(u.uPrev2, 3); gl.uniform1i(u.uPrev3, 4);
      gl.uniform2f(u.uRes, w, h); gl.uniform1i(u.uFrame, frame); gl.uniform1i(u.uSeed, opt.seed || 0);
      gl.uniform3fv(u.uEye, c.eye); gl.uniform3fv(u.uFwd, c.f); gl.uniform3fv(u.uRight, c.r); gl.uniform3fv(u.uUp, c.u);
      gl.uniform1f(u.uTanY, c.tanY); gl.uniform1f(u.uAspect, c.aspect); gl.uniform2fv(u.uShift, c.shift);
      gl.uniform1f(u.uFocus, c.focus); gl.uniform1f(u.uLens, c.lens); gl.uniform4fv(u.uL, lay);
      gl.uniform4fv(u.uA, bar.a); gl.uniform1f(u.uWZ, bar.wall);
      for (var s = 0; s < n; s++) {
        if (s) {
          gl.bindFramebuffer(gl.FRAMEBUFFER, fbo[1 - cur]);
          [tex[cur], geo[cur], grp[0][cur], grp[1][cur], grp[2][cur]].forEach(function (t, k) { gl.activeTexture(gl.TEXTURE0 + k); gl.bindTexture(gl.TEXTURE_2D, t); });
          gl.uniform1i(u.uFrame, frame);
        }
        gl.drawArrays(gl.TRIANGLES, 0, 3);
        cur = 1 - cur; frame++;
      }
      present(fade);
      if (q) { gl.endQuery(tq.TIME_ELAPSED_EXT); pending.push({ q: q, gen: gen }); }
      poll();
    }
    // mixes the groups of lights in their colours, denoises while the average is young, and shows it
    function present(fade) {
      var col = colours(time);
      gl.useProgram(cb.p);
      gl.bindFramebuffer(gl.FRAMEBUFFER, cfbo);
      gl.viewport(0, 0, w, h);
      [tex[cur], grp[0][cur], grp[1][cur], grp[2][cur]].forEach(function (t, k) { gl.activeTexture(gl.TEXTURE0 + k); gl.bindTexture(gl.TEXTURE_2D, t); });
      gl.uniform1i(cb.u.uS, 0); gl.uniform1i(cb.u.uG1, 1); gl.uniform1i(cb.u.uG2, 2); gl.uniform1i(cb.u.uG3, 3);
      gl.uniform3fv(cb.u.uC1, col.slice(0, 3)); gl.uniform3fv(cb.u.uC2, col.slice(3, 6)); gl.uniform3fv(cb.u.uC3, col.slice(6, 9));
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      var shown = ctex;
      if (frame < DENOISE_UNTIL && !opt.raw) {        // four passes, 1, 2, 4 and 8 pixels apart
        gl.useProgram(dn.p);
        gl.uniform1i(dn.u.uCol, 0); gl.uniform1i(dn.u.uGeo, 1); gl.uniform2f(dn.u.uRes, w, h); gl.uniform1f(dn.u.uN, frame);
        gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, geo[cur]); gl.activeTexture(gl.TEXTURE0);
        for (var k = 0; k < 4; k++) {
          gl.bindFramebuffer(gl.FRAMEBUFFER, dfbo[k & 1]);
          gl.bindTexture(gl.TEXTURE_2D, k === 0 ? ctex : dtex[(k - 1) & 1]);
          gl.uniform1i(dn.u.uStep, 1 << k); gl.uniform1i(dn.u.uFirst, k === 0 ? 1 : 0);
          gl.drawArrays(gl.TRIANGLES, 0, 3);
        }
        shown = dtex[1];
      }
      gl.useProgram(sh.p);
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
      gl.viewport(0, 0, w, h);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, shown);
      gl.uniform1i(sh.u.uAcc, 0); gl.uniform2f(sh.u.uRes, w, h); gl.uniform1f(sh.u.uFade, fade == null ? 1 : fade);
      gl.uniform1f(sh.u.uExposure, opt.exposure || 1.0);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    }
    function poll() {
      while (pending.length && gl.getQueryParameter(pending[0].q, gl.QUERY_RESULT_AVAILABLE)) {
        var p = pending.shift(), ns = gl.getQueryParameter(p.q, gl.QUERY_RESULT);
        if (p.gen === gen && !gl.getParameter(tq.GPU_DISJOINT_EXT)) { gpu.push(ns / 1e6); if (gpu.length > 9) gpu.shift(); }
        gl.deleteQuery(p.q);
      }
    }
    function gpuMs() {                // the median of the last few frames, 0 until five are in
      if (gpu.length < 5) return 0;
      var a = gpu.slice().sort(function (x, y) { return x - y; });
      return a[a.length >> 1];
    }
    function sync() {                 // wait for the GPU (reading from an offscreen buffer, not from the screen)
      var px = new Float32Array(4);
      gl.bindFramebuffer(gl.FRAMEBUFFER, fbo[cur]); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.FLOAT, px);
      gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    }
    function read(which) {            // for offline stills, bottom row first: the colour mixed at the current colours
      var out = new Float32Array(w * h * 4);   // (alpha: how much the samples vary), or with "geo" the first hits
      if (which === "geo") { gl.bindFramebuffer(gl.FRAMEBUFFER, fbo[cur]); gl.readBuffer(gl.COLOR_ATTACHMENT1); }
      else { present(1); gl.bindFramebuffer(gl.FRAMEBUFFER, cfbo); gl.readBuffer(gl.COLOR_ATTACHMENT0); }
      gl.readPixels(0, 0, w, h, gl.RGBA, gl.FLOAT, out); gl.readBuffer(gl.COLOR_ATTACHMENT0);
      return out;
    }
    return {
      size: size, step: step, present: present, retime: function () { gen++; gpu = []; }, gl: gl, read: read, sync: sync, gpuMs: gpuMs, timed: !!tq,
      get time() { return time; }, set time(t) { time = t; },
      get frame() { return frame; },
      turn: function (yaw) { view.yaw = yaw; frame = 0; },
      get yaw() { return view.yaw; }
    };
  }
  window.Studio = { make: make };

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
  // Resolution: as sharp as the GPU allows, up to the screen's own (at most ~4.5 million pixels): the pixel count is
  // set so a frame costs the GPU about 10 ms. That cost comes from timer queries where the browser has them, and
  // otherwise from a few frames timed while waiting for the GPU. Slow frame intervals alone are never the reason to
  // trace fewer pixels: browsers slow frames down on their own (a window in the background, power saving, a 30 Hz
  // display). In the first couple of seconds the size may also go up, as a GPU leaves its idle clocks.
  var spp = media.querySelector(".spp"), DONE = 512, budget = 0, slow = 0, times = [], onScreen = true, running = false, startedAt = 0;

  function native() {
    var box = media.getBoundingClientRect(), dpr = Math.min(window.devicePixelRatio || 1, 2);
    return { w: box.width * dpr, h: box.height * dpr };
  }
  function pixels() { return R.gl.drawingBufferWidth * R.gl.drawingBufferHeight; }
  function fit() {
    var n = native(), px = Math.min(n.w * n.h, 4.5e6, budget || 6e5);
    var k = Math.min(1, Math.sqrt(px / (n.w * n.h)));
    R.size(Math.max(2, Math.round(n.w * k)), Math.max(2, Math.round(n.h * k)));
  }
  function measure(fade) {                          // without timer queries: GPU time of one frame, in ms
    R.step(fade); R.sync();
    var t0 = performance.now();
    for (var i = 0; i < 3; i++) R.step(fade);
    R.sync();
    return Math.max(0.5, (performance.now() - t0) / 3);
  }
  function retarget(ms, up) {                       // a budget of ~10 ms per frame; true if the size changed
    var before = pixels(), want = Math.max(1.5e5, before * 10 / ms);
    if (want < before ? want > before * 0.85 : !up || want < before * 1.3) return false;
    budget = want; fit();
    return pixels() !== before;
  }
  function label() {
    if (spp) spp.textContent = R.frame.toLocaleString("en-US") + (R.frame === 1 ? " sample" : " samples") + " per pixel.";
  }
  var last = 0, tick = 0, spf = 1, iv = 0;
  // samples per frame: once the picture is at the screen's resolution and a sample costs well under the budget, several
  // are traced each frame (up to ~10 ms of GPU work), so a fast GPU converges in seconds rather than half a minute
  function pace(ms, early) {
    var per = ms / spf;
    if (early && retarget(per, true)) return;          // first the resolution (a new size restarts the timing)
    // too slow: fewer samples per frame first, then fewer pixels. Only while the browser runs at its full frame rate:
    // when it slows the page down (a window in the background), the GPU idles at low clocks and every frame times long
    if (!early && ms > 20 && slow < 6 && iv && iv < 40) {
      slow++;
      if (spf > 1) { spf = Math.max(1, Math.floor(10 / per)); R.retime(); } else retarget(per);
      return;
    }
    if (pixels() >= native().w * native().h * 0.9 || pixels() >= 4.4e6) {
      var want = Math.max(1, Math.min(8, Math.floor(10 / per)));
      if (want !== spf) { spf = want; R.retime(); }
    }
  }
  function frame(t) {
    if (!onScreen || document.hidden) { running = false; return; }
    if (!startedAt) { startedAt = t; media.classList.add("live"); }
    var fade = Math.min(1, (t - startedAt) / 500);
    R.time = 1.3 + (t - startedAt) / 1000;               // the lights' colours keep flowing
    if (R.frame < DONE) {
      R.step(fade, Math.min(spf, DONE - R.frame));
      if (R.timed) {
        var ms = R.gpuMs();
        if (ms) pace(ms, t - startedAt < 2500);
      } else if (last) {                              // slow frames: time the GPU before tracing fewer pixels
        times.push(t - last);
        if (times.length === 12) {
          times.sort(function (a, b) { return a - b; });
          if (times[6] > 34 && slow < 6) { var m = measure(fade); if (m > 20) { slow++; retarget(m); } }
          times = [];
        }
      }
      label();
      if (R.frame >= DONE) media.classList.add("done");
    } else if (++tick % 3 === 0) R.present(1);        // converged: nothing is traced; the colours are mixed anew ~20 times a second
    if (last) iv = iv ? iv * 0.8 + (t - last) * 0.2 : t - last;
    last = t;
    requestAnimationFrame(frame);
  }
  function go() {
    if (running || !onScreen || document.hidden) return;
    running = true; last = 0; times = []; requestAnimationFrame(frame);
  }
  fit();
  if (!R.timed) try { budget = Math.max(1.5e5, pixels() * 10 / measure(0)); fit(); } catch (e) { budget = 6e5; fit(); }
  window.addEventListener("resize", function () { fit(); go(); });
  document.addEventListener("visibilitychange", go);
  if ("IntersectionObserver" in window) new IntersectionObserver(function (e) { onScreen = e[0].isIntersecting; go(); }).observe(media);

  // dragging sideways turns the camera (vertical drags still scroll the page on touch screens)
  var down = null;
  canvas.addEventListener("pointerdown", function (e) { down = { x: e.clientX, yaw: R.yaw }; canvas.setPointerCapture(e.pointerId); media.classList.add("dragging"); });
  canvas.addEventListener("pointermove", function (e) {
    if (!down) return;
    var yaw = Math.max(-0.55, Math.min(0.55, down.yaw - (e.clientX - down.x) / 420));
    if (yaw !== R.yaw) { R.turn(yaw); media.classList.remove("done"); go(); }
  });
  function up() { down = null; media.classList.remove("dragging"); }
  canvas.addEventListener("pointerup", up); canvas.addEventListener("pointercancel", up);
  go();
})();
