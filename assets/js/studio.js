/* The home page opening: a small studio scene, path traced live in the browser (WebGL2, no libraries).

   Scene: a red neon ring standing on a wet black floor, a brass sphere cut into a gyroid lattice floating in it,
   a glass sphere to the left and a chrome one to the right, a cool neon tube standing to the left, haze in the air.

   Rendering, per pixel and frame: one camera path through a thin lens, averaged into the image so the picture
   starts as noise and converges.
   - Surfaces: GGX microfacet reflection (brass, chrome, the floor's clear coat) with Smith shadowing and Schlick
     Fresnel; matte under-layers; glass with Fresnel reflection and refraction.
   - Lights: the ring and the tube, each sampled over its surface, by next-event estimation; on the brass, light
     sampling and BRDF sampling are combined with multiple importance sampling (power heuristic).
   - Spectral dispersion: a path that reaches the glass picks a wavelength; the index of refraction follows Cauchy's
     law and the path is weighted by that wavelength's colour (CIE 1931), so the glass splits light into colours.
   - Participating media: homogeneous haze with free-flight distance sampling, a Henyey-Greenstein phase function
     and light sampling at every scattering event, which is what draws the beams through the lattice.
   - Geometry: analytic spheres and planes; the ring (a thin torus) and the lattice ray-marched as signed distance fields.
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
    "uniform vec2 uRes; uniform int uFrame; uniform sampler2D uPrev;",
    "uniform vec3 uEye, uFwd, uRight, uUp; uniform float uTanY, uAspect, uFocus, uLens; uniform vec2 uShift;",
    "out vec4 oColor;",
    "#define PI 3.14159265",
    "const float EPS = 1e-4;",
    // the scene
    "const vec3 RING_C = vec3(0.30, 1.19, -0.62); const float RING_R = 1.12, RING_T = 0.034;",
    "const vec3 RING_E = vec3(15.0, 2.6, 1.15);                       // neon, red-orange",
    "const vec3 GY_C = vec3(0.30, 1.17, -0.45); const float GY_R = 0.6;  // the gyroid sphere",
    "const vec3 GLASS_C = vec3(-1.45, 0.47, 0.5); const float GLASS_R = 0.47;",
    "const vec3 CHROME_C = vec3(1.8, 0.28, 0.72); const float CHROME_R = 0.28;",
    "const vec2 TUBE_XZ = vec2(-3.15, -1.3); const float TUBE_R = 0.036, TUBE_H = 2.7;   // a standing neon tube",
    "const vec3 TUBE_E = vec3(3.2, 5.4, 9.5);                         // cool blue-white",
    "const vec3 KEY_C = vec3(0.0, 4.4, -0.9); const vec2 KEY_S = vec2(2.0, 1.2);   // overhead key light, facing down",
    "const vec3 KEY_E = vec3(2.9, 2.8, 2.65);",
    "const float SIG = 0.008, HG = 0.75;                             // haze density, forward scattering",
    "const vec3 MED_C = vec3(0., 1., 0.); const float MED_R = 11.;    // the haze fills this sphere",
    "const float P_RING = 0.45, P_TUBE = 0.25;                        // how often each light is sampled (the key: the rest)",
    "const vec3 WL[31] = vec3[31](vec3(0.009, 0.000, 0.178), vec3(0.090, 0.000, 0.601), vec3(0.209, 0.000, 1.921), vec3(0.304, 0.000, 4.079), vec3(0.457, 0.000, 5.102), vec3(0.297, 0.000, 5.229), vec3(0.000, 0.000, 4.886), vec3(0.000, 0.094, 3.756), vec3(0.000, 0.512, 2.300), vec3(0.000, 1.007, 1.245), vec3(0.000, 1.621, 0.608), vec3(0.000, 2.415, 0.178), vec3(0.000, 3.281, 0.000), vec3(0.000, 3.841, 0.000), vec3(0.000, 3.945, 0.000), vec3(0.000, 3.760, 0.000), vec3(0.732, 3.318, 0.000), vec3(1.779, 2.690, 0.000), vec3(2.798, 1.937, 0.000), vec3(3.640, 1.149, 0.000), vec3(4.170, 0.434, 0.000), vec3(4.213, 0.000, 0.000), vec3(3.737, 0.000, 0.000), vec3(2.937, 0.000, 0.000), vec3(2.055, 0.000, 0.000), vec3(1.283, 0.000, 0.000), vec3(0.714, 0.000, 0.000), vec3(0.354, 0.000, 0.000), vec3(0.156, 0.000, 0.000), vec3(0.060, 0.007, 0.000), vec3(0.020, 0.007, 0.000));",
    "const int NONE = 0, FLOOR = 1, RING = 2, TUBE = 3, GYROID = 4, GLASS = 5, CHROME = 6, KEY = 7;",
    "uint rs;",
    "uint hash(uint x){ x ^= x >> 16; x *= 0x7feb352du; x ^= x >> 15; x *= 0x846ca68bu; x ^= x >> 16; return x; }",
    "float rnd(){ rs = rs * 747796405u + 2891336453u; uint w = ((rs >> ((rs >> 28u) + 4u)) ^ rs) * 277803737u; w = (w >> 22u) ^ w; return float(w) * (1.0 / 4294967296.0); }",
    "vec3 specw(float l) { float x = clamp((l - 400.) / 10., 0., 29.999); int i = int(x); return mix(WL[i], WL[i + 1], x - float(i)); }",

    // signed distance to the gyroid sphere
    "float gyroid(vec3 p) {",
    "  vec3 q = (p - GY_C) * 10.;",
    "  float g = abs(dot(sin(q), cos(q.yzx))) / 10. - 0.014;            // a thin sheet along the gyroid surface",
    "  return max(length(p - GY_C) - GY_R, g * 0.55);                   // ... cut to a sphere",
    "}",
    "vec3 gyroidNormal(vec3 p) {",
    "  const vec2 k = vec2(1., -1.) * 5e-4;",
    "  return normalize(k.xyy * gyroid(p + k.xyy) + k.yyx * gyroid(p + k.yyx) + k.yxy * gyroid(p + k.yxy) + k.xxx * gyroid(p + k.xxx));",
    "}",
    "vec2 sphereSpan(vec3 ro, vec3 rd, vec3 c, float r) {",
    "  vec3 oc = ro - c; float b = dot(oc, rd), h = b * b - dot(oc, oc) + r * r;",
    "  if (h < 0.) return vec2(1e9, -1e9); h = sqrt(h); return vec2(-b - h, -b + h);",
    "}",
    "bool marchGyroid(vec3 ro, vec3 rd, float tmax, out float t) {",
    "  vec2 s = sphereSpan(ro, rd, GY_C, GY_R + 0.002);",
    "  float t0 = max(s.x, EPS * 10.), t1 = min(s.y, tmax);",
    "  if (t0 >= t1) return false;",
    "  t = t0;",
    "  for (int i = 0; i < 140; i++) {",
    "    float d = gyroid(ro + rd * t);",
    "    if (d < 2e-4) return true;",
    "    t += d; if (t > t1) return false;",
    "  }",
    "  return false;",
    "}",
    // ring: a torus in the plane z = RING_C.z; traced as a thin tube by marching its distance function
    "float ringDist(vec3 p) { vec3 q = p - RING_C; return length(vec2(length(q.xy) - RING_R, q.z)) - RING_T; }",
    "bool marchRing(vec3 ro, vec3 rd, float tmax, out float t) {",
    "  vec2 s = sphereSpan(ro, rd, RING_C, RING_R + RING_T + 0.01);",
    "  float t0 = max(s.x, EPS * 10.), t1 = min(s.y, tmax);",
    "  if (t0 >= t1) return false;",
    "  t = t0;",
    "  for (int i = 0; i < 90; i++) {",
    "    float d = ringDist(ro + rd * t);",
    "    if (d < 1e-4) return true;",
    "    t += d; if (t > t1) return false;",
    "  }",
    "  return false;",
    "}",
    "bool ball(vec3 ro, vec3 rd, vec3 c, float r, inout float t, inout vec3 n, inout bool inside) {",
    "  vec2 s = sphereSpan(ro, rd, c, r); bool ins = false; float u = s.x;",
    "  if (u < EPS) { u = s.y; ins = true; }",
    "  if (u < EPS || u >= t) return false;",
    "  t = u; n = (ro + rd * u - c) / r; if (ins) n = -n; inside = ins; return true;",
    "}",
    // nearest surface; n faces the incoming ray except inside glass
    "int trace(vec3 ro, vec3 rd, float tmax, out float t, out vec3 n, out bool inside) {",
    "  t = tmax; n = vec3(0.); inside = false; int m = NONE; float s;",
    "  if (rd.y < 0.) { s = -ro.y / rd.y; if (s > EPS && s < t) { t = s; n = vec3(0., 1., 0.); m = FLOOR; } }",
    "  { vec2 o = ro.xz - TUBE_XZ, d = rd.xz; float a = dot(d, d), b = dot(o, d), c = dot(o, o) - TUBE_R * TUBE_R, h = b * b - a * c;",
    "    if (a > 1e-8 && h > 0.) { s = (-b - sqrt(h)) / a; float y = ro.y + rd.y * s;",
    "      if (s > EPS && s < t && y > 0. && y < TUBE_H) { t = s; n = vec3((o + d * s) / TUBE_R, 0.).xzy; n = vec3(n.x, 0., n.y); m = TUBE; } } }",
    "  if (rd.y > 0.) { s = (KEY_C.y - ro.y) / rd.y; vec3 p = ro + rd * s;",
    "    if (s > EPS && s < t && abs(p.x - KEY_C.x) < KEY_S.x && abs(p.z - KEY_C.z) < KEY_S.y) { t = s; n = vec3(0., -1., 0.); m = KEY; } }",
    "  bool ins = false;",
    "  if (ball(ro, rd, GLASS_C, GLASS_R, t, n, ins)) { m = GLASS; inside = ins; }",
    "  if (ball(ro, rd, CHROME_C, CHROME_R, t, n, ins)) { m = CHROME; inside = false; }",
    "  if (marchRing(ro, rd, t, s)) { t = s; vec3 q = ro + rd * s - RING_C; vec2 a = normalize(q.xy) * RING_R; n = normalize(q - vec3(a, 0.)); m = RING; }",
    "  if (marchGyroid(ro, rd, t, s)) { t = s; n = gyroidNormal(ro + rd * s); if (dot(n, rd) > 0.) n = -n; m = GYROID; }",
    "  return m;",
    "}",
    "bool visible(vec3 a, vec3 b) {          // nothing opaque between two points (the glass counts as opaque here)",
    "  vec3 d = b - a; float l = length(d); d /= l; float t; vec3 n; bool i;",
    "  int m = trace(a, d, l - 2e-3, t, n, i);",
    "  return m == NONE;",
    "}",
    "vec3 ortho(vec3 n) { return normalize(cross(abs(n.x) > .5 ? vec3(0., 1., 0.) : vec3(1., 0., 0.), n)); }",
    "vec3 cosdir(vec3 n) { float a = 2. * PI * rnd(), r2 = rnd(), r = sqrt(r2); vec3 u = ortho(n), v = cross(n, u); return normalize(u * cos(a) * r + v * sin(a) * r + n * sqrt(1. - r2)); }",
    // GGX
    "float D_ggx(float nh, float a) { float a2 = a * a, d = nh * nh * (a2 - 1.) + 1.; return a2 / (PI * d * d); }",
    "float G1(float nv, float a) { float a2 = a * a; return 2. * nv / (nv + sqrt(a2 + (1. - a2) * nv * nv)); }",
    "vec3 schlick(vec3 f0, float c) { return f0 + (1. - f0) * pow(1. - c, 5.); }",
    "vec3 ggxHalf(vec3 n, float a) { float u = rnd(), th = atan(a * sqrt(u / (1. - u))), ph = 2. * PI * rnd(); vec3 t = ortho(n), b = cross(n, t); return normalize(t * cos(ph) * sin(th) + b * sin(ph) * sin(th) + n * cos(th)); }",
    // light sampling: a point on the ring or the softbox; returns radiance, fills direction, distance and pdf (solid angle)
    "vec3 sampleLight(vec3 p, out vec3 wi, out float dist, out float pdf) {",
    "  vec3 lp, ln, Le; float area, sel, x = rnd();",
    "  if (x < P_RING) {",
    "    float u = 2. * PI * rnd(), v = 2. * PI * rnd(); vec3 r = vec3(cos(u), sin(u), 0.);",
    "    ln = cos(v) * r + vec3(0., 0., sin(v)); lp = RING_C + r * RING_R + ln * RING_T;",
    "    area = 4. * PI * PI * RING_R * RING_T; Le = RING_E; sel = P_RING;",
    "  } else if (x < P_RING + P_TUBE) {",
    "    float u = 2. * PI * rnd(); ln = vec3(cos(u), 0., sin(u)); lp = vec3(TUBE_XZ.x, TUBE_H * rnd(), TUBE_XZ.y) + ln * TUBE_R;",
    "    area = 2. * PI * TUBE_R * TUBE_H; Le = TUBE_E; sel = P_TUBE;",
    "  } else {",
    "    lp = KEY_C + vec3((rnd() * 2. - 1.) * KEY_S.x, 0., (rnd() * 2. - 1.) * KEY_S.y); ln = vec3(0., -1., 0.);",
    "    area = 4. * KEY_S.x * KEY_S.y; Le = KEY_E; sel = 1. - P_RING - P_TUBE;",
    "  }",
    "  vec3 d = lp - p; float d2 = dot(d, d); dist = sqrt(d2); wi = d / dist;",
    "  float cl = dot(-wi, ln); if (cl <= 0.) { pdf = 0.; return vec3(0.); }",
    "  pdf = sel * d2 / (cl * area);",
    "  if (!visible(p, lp)) return vec3(0.);",
    "  return Le * exp(-SIG * dist);",
    "}",
    "float lightPdf(int m, vec3 wi, float dist, vec3 ln) {             // pdf of having sampled this point of light m",
    "  float cl = abs(dot(wi, ln)); if (cl < 1e-4) return 0.;",
    "  float a = m == RING ? P_RING / (4. * PI * PI * RING_R * RING_T) : m == TUBE ? P_TUBE / (2. * PI * TUBE_R * TUBE_H) : (1. - P_RING - P_TUBE) / (4. * KEY_S.x * KEY_S.y);",
    "  return a * dist * dist / cl;",
    "}",
    // materials sampled with MIS: the floor (clear coat over a dark base) and the brass
    "vec3 bsdf(int m, vec3 n, vec3 wo, vec3 wi, out float pdf) {",
    "  float nwo = max(1e-4, dot(n, wo)), nwi = dot(n, wi); pdf = 0.;",
    "  if (nwi <= 0.) return vec3(0.);",
    "  vec3 h = normalize(wi + wo); float nh = max(0., dot(n, h)), hw = max(1e-4, dot(h, wo));",
    "  if (m == GYROID) {",
    "    const float a = .26; float D = D_ggx(nh, a); pdf = D * nh / (4. * hw);",
    "    return D * G1(nwo, a) * G1(nwi, a) * schlick(vec3(.95, .72, .38), hw) / (4. * nwo * nwi);",
    "  }",
    "  const float a = .022; float D = D_ggx(nh, a), pc = .04 + .96 * pow(1. - nwo, 5.);",
    "  pdf = pc * D * nh / (4. * hw) + (1. - pc) * nwi / PI;",
    "  return vec3(D * G1(nwo, a) * G1(nwi, a) * (.04 + .96 * pow(1. - hw, 5.)) / (4. * nwo * nwi)) + (1. - pc) * vec3(.018, .018, .02) / PI;",
    "}",
    "vec3 bsdfDir(int m, vec3 n, vec3 wo) {",
    "  if (m == GYROID) return reflect(-wo, ggxHalf(n, .26));",
    "  float pc = .04 + .96 * pow(1. - max(0., dot(n, wo)), 5.);",
    "  return rnd() < pc ? reflect(-wo, ggxHalf(n, .022)) : cosdir(n);",
    "}",
    "float hgPhase(float c) { float g2 = HG * HG; return (1. - g2) / (4. * PI * pow(1. + g2 - 2. * HG * c, 1.5)); }",
    "vec3 hgSample(vec3 d) {",
    "  float g2 = HG * HG, s = (1. - g2) / (1. - HG + 2. * HG * rnd()), c = (1. + g2 - s * s) / (2. * HG);",
    "  float sn = sqrt(max(0., 1. - c * c)), ph = 2. * PI * rnd(); vec3 t = ortho(d), b = cross(d, t);",
    "  return normalize(t * cos(ph) * sn + b * sin(ph) * sn + d * c);",
    "}",

    "vec3 radiance(vec3 ro, vec3 rd, float lambda) {",
    "  vec3 L = vec3(0.), T = vec3(1.);",
    "  int mode = 0;                 // how we got here: 0 camera or specular, 1 matte or medium (light already sampled), 2 brass (MIS)",
    "  float lastPdf = 0.; bool split = false;",
    "  for (int b = 0; b < 8; b++) {",
    "    float t; vec3 n; bool inside;",
    "    vec2 med = sphereSpan(ro, rd, MED_C, MED_R);",
    "    int m = trace(ro, rd, max(med.y, EPS), t, n, inside);",
    "    float tf = -log(1. - rnd()) / SIG;                      // free flight through the haze",
    "    if (tf < t && tf < med.y) {",
    "      vec3 p = ro + rd * tf, wi; float dist, pdf;",
    "      vec3 Le = sampleLight(p, wi, dist, pdf);",
    "      if (pdf > 0.) L += T * Le * hgPhase(dot(rd, wi)) / pdf;",
    "      ro = p; rd = hgSample(rd); mode = 1; continue;",
    "    }",
    "    if (m == NONE) break;",
    "    vec3 p = ro + rd * t;",
    "    if (m == RING || m == TUBE || m == KEY) {",
    "      vec3 Le = m == RING ? RING_E : m == TUBE ? TUBE_E : KEY_E;",
    "      if (mode == 0) L += T * Le;",
    "      else if (mode == 2) { float pl = lightPdf(m, rd, t, n); L += T * Le * lastPdf * lastPdf / (lastPdf * lastPdf + pl * pl); }",
    "      break;",
    "    }",
    "    vec3 wo = -rd;",
    "    if (m == FLOOR || m == GYROID) {                           // light sampling and BSDF sampling, combined by MIS",
    "      vec3 q = p + n * 1e-3, wi; float dist, pl, pb;",
    "      vec3 Le = sampleLight(q, wi, dist, pl);",
    "      if (pl > 0.) { vec3 f = bsdf(m, n, wo, wi, pb); if (pb > 0.) L += T * Le * f * dot(n, wi) / pl * (pl * pl / (pl * pl + pb * pb)); }",
    "      rd = bsdfDir(m, n, wo);",
    "      vec3 f = bsdf(m, n, wo, rd, pb);",
    "      if (pb <= 0.) break;",
    "      T *= f * dot(n, rd) / pb; lastPdf = pb; mode = 2; ro = q;",
    "    } else if (m == CHROME) {",
    "      vec3 h = ggxHalf(n, .02); vec3 r = reflect(rd, h); if (dot(r, n) <= 0.) r = reflect(rd, n);",
    "      T *= schlick(vec3(.92, .93, .95), max(0., dot(n, wo))); rd = r; ro = p + n * 1e-3; mode = 0;",
    "    } else {                                                   // glass, dispersive",
    "      if (!split) { split = true; T *= specw(lambda); }",
    "      float lu = lambda * 1e-3, ior = 1.47 + .0110 / (lu * lu);",
    "      float eta = inside ? ior : 1. / ior, c = dot(wo, n); vec3 tr = refract(rd, n, eta);",
    "      float r0 = (ior - 1.) / (ior + 1.); r0 *= r0;",
    "      float F = dot(tr, tr) < .5 ? 1. : r0 + (1. - r0) * pow(1. - (inside ? -dot(tr, n) : c), 5.);",
    "      if (rnd() < F) { rd = reflect(rd, n); ro = p + n * 1e-3; } else { rd = tr; ro = p - n * 1e-3; }",
    "      mode = 0;",
    "    }",
    "    if (b > 2) { float q = clamp(max(T.x, max(T.y, T.z)), .05, .95); if (rnd() > q) break; T /= q; }",
    "  }",
    "  return L;",
    "}",
    "void main() {",
    "  uvec2 px = uvec2(gl_FragCoord.xy);",
    "  rs = hash(px.x ^ hash(px.y ^ hash(uint(uFrame) * 2654435761u)));",
    "  float lambda = 400. + 300. * fract(float(uFrame) * .618034 + rnd());   // stratified over frames",
    "  vec2 ndc = (gl_FragCoord.xy + vec2(rnd(), rnd()) - .5) / uRes * 2. - 1. - uShift;",
    "  vec3 dir = normalize(uFwd + uRight * ndc.x * uTanY * uAspect + uUp * ndc.y * uTanY);",
    "  vec3 focus = uEye + dir * (uFocus / dot(dir, uFwd));",
    "  float a = 2. * PI * rnd(), r = uLens * sqrt(rnd());",
    "  vec3 eye = uEye + (uRight * cos(a) + uUp * sin(a)) * r;",
    "  vec3 c = radiance(eye, normalize(focus - eye), lambda);",
    "  float lum = dot(c, vec3(.2126, .7152, .0722)); if (lum > 10.) c *= 10. / lum;   // tame fireflies",
    "  vec3 prev = uFrame == 0 ? vec3(0.) : texelFetch(uPrev, ivec2(px), 0).rgb;",
    "  oColor = vec4(mix(prev, c, 1. / float(uFrame + 1)), 1.);",
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
    var tr, sh;
    try { tr = program(gl, TRACE); sh = program(gl, SHOW); } catch (e) { if (opt.log) opt.log(String(e)); return null; }
    var buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    var tex = [], fbo = [], w = 0, h = 0, frame = 0, cur = 0;
    var view = { yaw: 0, pitch: 6.5 * Math.PI / 180 };

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
    // framing: wide pictures show the whole set with the ring right of centre; tall ones close in on the ring
    function camera() {
      var aspect = w / h, tanY = Math.tan(17 * Math.PI / 180), wide = aspect > 1.15;
      var target = wide ? [-0.05, 0.85, -0.45] : [0.2, 1.05, -0.5];
      var dist = wide ? Math.max(8.2, 4.4 / (tanY * aspect)) : Math.max(4.8, 1.9 / (tanY * aspect));
      var shift = wide ? [0.04, -0.02] : [0, 0.24];
      var cy = Math.cos(view.yaw), sy = Math.sin(view.yaw), cp = Math.cos(view.pitch), sp = Math.sin(view.pitch);
      var eye = [target[0] + dist * sy * cp, target[1] + dist * sp, target[2] + dist * cy * cp];
      var f = norm([target[0] - eye[0], target[1] - eye[1], target[2] - eye[2]]);
      var r = norm([-f[2], 0, f[0]]), u = [r[1] * f[2] - r[2] * f[1], r[2] * f[0] - r[0] * f[2], r[0] * f[1] - r[1] * f[0]];
      var gc = [0.3 - eye[0], 1.17 - eye[1], -0.45 - eye[2]];
      return { eye: eye, f: f, r: r, u: u, tanY: tanY, aspect: aspect, shift: shift, focus: gc[0] * f[0] + gc[1] * f[1] + gc[2] * f[2], lens: 0.045 };
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
      gl.uniform1f(sh.u.uExposure, opt.exposure || 1.0);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
    }
    return {
      size: size, step: step, gl: gl,
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
  var spp = media.querySelector(".spp"), DONE = 1024, scale = 1, slow = 0, times = [], onScreen = true, running = false, startedAt = 0;

  function fit() {
    var box = media.getBoundingClientRect(), dpr = Math.min(window.devicePixelRatio || 1, 2);
    var k = Math.min(1, Math.sqrt(1.0e6 / (box.width * box.height * dpr * dpr))) * scale;   // at most ~1 million pixels
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
      if (times.length === 12) {                    // judged on the middle of a dozen frames
        times.sort(function (a, b) { return a - b; });
        if (times[6] > 30 && slow < 4) { slow++; scale *= 0.72; fit(); }
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
