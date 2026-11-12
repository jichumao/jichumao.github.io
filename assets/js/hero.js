// Home hero: the artwork is drawn with a small WebGL fragment shader so the paint slowly drifts
// and bends away from the pointer. Without WebGL, or when the visitor prefers reduced motion,
// the plain <img> underneath stays visible and nothing here runs.
(function () {
  var media = document.querySelector(".hero-media");
  if (!media) return;
  var img = media.querySelector(".hero-art");
  var canvas = media.querySelector(".hero-canvas");
  if (!img || !canvas) return;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  var gl = canvas.getContext("webgl", { antialias: false, alpha: false, powerPreference: "low-power" });
  if (!gl) return;

  var VERT = "attribute vec2 p; varying vec2 uv; void main(){ uv = p * .5 + .5; uv.y = 1. - uv.y; gl_Position = vec4(p, 0., 1.); }";
  var FRAG = [
    "precision highp float;",
    "varying vec2 uv;",
    "uniform sampler2D tex;",
    "uniform vec2 res, img, mouse;",   // canvas size, image size (px), pointer in canvas uv
    "uniform float time, hover;",
    "float hash(vec2 p){ return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }",
    "float noise(vec2 p){ vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);",
    "  return mix(mix(hash(i), hash(i + vec2(1., 0.)), f.x), mix(hash(i + vec2(0., 1.)), hash(i + vec2(1., 1.)), f.x), f.y); }",
    "float fbm(vec2 p){ float a = .5, s = 0.; for (int i = 0; i < 3; i++){ s += a * noise(p); p = p * 2.03 + 11.7; a *= .5; } return s; }",
    "void main(){",
    // same framing as CSS `object-fit: cover; object-position: 85% 47%`
    "  float rc = res.x / res.y, ri = img.x / img.y;",
    "  vec2 win = rc > ri ? vec2(1., ri / rc) : vec2(rc / ri, 1.);",
    "  vec2 st = (1. - win) * vec2(.85, .47) + uv * win;",
    "  vec2 p = vec2(st.x * ri, st.y) * 1.7;",
    // slow curl-like drift, strongest where the paint is bright
    "  vec2 flow = vec2(fbm(p + vec2(0., time * .045)), fbm(p + vec2(5.2, -time * .038))) - .5;",
    "  float lum = dot(texture2D(tex, st).rgb, vec3(.3, .59, .11));",
    "  vec2 d = flow * .016 * smoothstep(.02, .35, lum);",
    // the paint leans away from the pointer
    "  vec2 m = uv - mouse; m.x *= rc;",
    "  float fall = exp(-dot(m, m) * 9.) * hover;",
    "  d -= normalize(m + 1e-4) * fall * .014 * vec2(win.x / rc, win.y);",
    "  vec3 c = texture2D(tex, st + d).rgb;",
    "  c += c * fall * .18;",
    "  gl_FragColor = vec4(c, 1.);",
    "}"
  ].join("\n");

  function shader(type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src); gl.compileShader(s);
    return gl.getShaderParameter(s, gl.COMPILE_STATUS) ? s : null;
  }
  var vs = shader(gl.VERTEX_SHADER, VERT), fs = shader(gl.FRAGMENT_SHADER, FRAG);
  if (!vs || !fs) return;
  var prog = gl.createProgram();
  gl.attachShader(prog, vs); gl.attachShader(prog, fs); gl.linkProgram(prog);
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) return;
  gl.useProgram(prog);

  gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  var loc = gl.getAttribLocation(prog, "p");
  gl.enableVertexAttribArray(loc);
  gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);

  var u = {};
  ["res", "img", "mouse", "time", "hover"].forEach(function (n) { u[n] = gl.getUniformLocation(prog, n); });

  var ready = false, visible = true, raf = 0, last = 0;
  var mouse = [0.75, 0.5], target = [0.75, 0.5], hover = 0, hoverTarget = 0;
  var start = performance.now();

  function upload() {
    var t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    try {
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, img);
    } catch (e) { return; }
    gl.uniform2f(u.img, img.naturalWidth, img.naturalHeight);
    ready = true;
    resize();
    media.classList.add("live");
    loop();
  }

  function resize() {
    var dpr = Math.min(window.devicePixelRatio || 1, 1.5);
    var w = Math.max(1, Math.round(canvas.clientWidth * dpr)), h = Math.max(1, Math.round(canvas.clientHeight * dpr));
    if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
    gl.viewport(0, 0, w, h);
    gl.uniform2f(u.res, w, h);
  }

  function draw() {
    mouse[0] += (target[0] - mouse[0]) * 0.06;
    mouse[1] += (target[1] - mouse[1]) * 0.06;
    hover += (hoverTarget - hover) * 0.05;
    gl.uniform2f(u.mouse, mouse[0], mouse[1]);
    gl.uniform1f(u.hover, hover);
    gl.uniform1f(u.time, (performance.now() - start) / 1000);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  }
  function loop() {
    cancelAnimationFrame(raf);
    if (!ready || !visible || document.hidden) return;
    var now = performance.now();
    if (now - last > 30) { last = now; draw(); }   // the drift is slow: ~30 fps is plenty
    raf = requestAnimationFrame(loop);
  }

  var hero = media.parentNode;
  hero.addEventListener("pointermove", function (e) {
    var r = canvas.getBoundingClientRect();
    target[0] = (e.clientX - r.left) / r.width;
    target[1] = (e.clientY - r.top) / r.height;
    hoverTarget = 1;
  });
  hero.addEventListener("pointerleave", function () { hoverTarget = 0; });
  window.addEventListener("resize", function () { if (ready) { resize(); draw(); } });
  document.addEventListener("visibilitychange", loop);
  if ("IntersectionObserver" in window) {
    new IntersectionObserver(function (entries) { visible = entries[0].isIntersecting; loop(); }).observe(canvas);
  }
  canvas.addEventListener("webglcontextlost", function (e) { e.preventDefault(); ready = false; media.classList.remove("live"); });

  if (img.complete && img.naturalWidth) upload(); else img.addEventListener("load", upload);
})();
