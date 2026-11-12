// The opening picture is the Procedural Fireball project running live: its own GLSL
// (assets/shaders/fireball.vert.glsl and fireball.frag.glsl, copied unchanged from the
// project's repository) on a subdivided icosphere, with the project's default colours,
// amplitude, frequency and time speed. Without WebGL 2 the still picture underneath stays.
(function () {
  "use strict";
  var cv = document.querySelector(".hero-canvas");
  if (!cv || !window.Promise || !window.fetch) return;
  var box = cv.parentNode;
  var gl = cv.getContext("webgl2", { alpha: true, antialias: true, premultipliedAlpha: false });
  if (!gl) return;
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var dir = cv.getAttribute("data-shaders");
  var text = function (r) { if (!r.ok) throw new Error(r.status); return r.text(); };

  function icosphere(levels) {
    var t = (1 + Math.sqrt(5)) / 2, v = [], f = [], mid = {};
    var add = function (x, y, z) { var l = Math.sqrt(x * x + y * y + z * z); v.push(x / l, y / l, z / l); return v.length / 3 - 1; };
    [[-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0], [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t], [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]]
      .forEach(function (p) { add(p[0], p[1], p[2]); });
    f = [0, 11, 5, 0, 5, 1, 0, 1, 7, 0, 7, 10, 0, 10, 11, 1, 5, 9, 5, 11, 4, 11, 10, 2, 10, 7, 6, 7, 1, 8,
         3, 9, 4, 3, 4, 2, 3, 2, 6, 3, 6, 8, 3, 8, 9, 4, 9, 5, 2, 4, 11, 6, 2, 10, 8, 6, 7, 9, 8, 1];
    var half = function (a, b) {
      var k = a < b ? a + "_" + b : b + "_" + a;
      if (!(k in mid)) mid[k] = add(v[a * 3] + v[b * 3], v[a * 3 + 1] + v[b * 3 + 1], v[a * 3 + 2] + v[b * 3 + 2]);
      return mid[k];
    };
    for (var n = 0; n < levels; n++) {
      var g = [];
      for (var i = 0; i < f.length; i += 3) {
        var a = f[i], b = f[i + 1], c = f[i + 2], ab = half(a, b), bc = half(b, c), ca = half(c, a);
        g.push(a, ab, ca, b, bc, ab, c, ca, bc, ab, bc, ca);
      }
      f = g;
    }
    return { pos: v, idx: f };
  }

  function shader(type, src) {
    var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    return s;
  }

  Promise.all([fetch(dir + "fireball.vert.glsl").then(text), fetch(dir + "fireball.frag.glsl").then(text)]).then(function (src) {
    var p = gl.createProgram();
    gl.attachShader(p, shader(gl.VERTEX_SHADER, src[0])); gl.attachShader(p, shader(gl.FRAGMENT_SHADER, src[1]));
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    gl.useProgram(p);

    var m = icosphere(5), n = m.pos.length / 3, pos = new Float32Array(n * 4), nor = new Float32Array(n * 4);
    for (var i = 0; i < n; i++) {
      pos[i * 4] = nor[i * 4] = m.pos[i * 3]; pos[i * 4 + 1] = nor[i * 4 + 1] = m.pos[i * 3 + 1]; pos[i * 4 + 2] = nor[i * 4 + 2] = m.pos[i * 3 + 2];
      pos[i * 4 + 3] = 1;
    }
    var attr = function (name, data) {
      var l = gl.getAttribLocation(p, name); if (l < 0) return;
      gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer()); gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW);
      gl.enableVertexAttribArray(l); gl.vertexAttribPointer(l, 4, gl.FLOAT, false, 0, 0);
    };
    attr("vs_Pos", pos); attr("vs_Nor", nor);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(m.idx), gl.STATIC_DRAW);

    var U = function (name) { return gl.getUniformLocation(p, name); };
    var id = new Float32Array([1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]);
    gl.uniformMatrix4fv(U("u_Model"), false, id); gl.uniformMatrix4fv(U("u_ModelInvTr"), false, id);
    gl.uniform4f(U("u_Color1"), 1, 128 / 255, 0, 1); gl.uniform4f(U("u_Color2"), 1, 1, 0, 1); gl.uniform4f(U("u_Color3"), 1, 0, 0, 1);
    gl.uniform1f(U("u_Amplitude"), 0.3); gl.uniform1f(U("u_Frequency"), 3.0);
    gl.enable(gl.DEPTH_TEST); gl.clearColor(0, 0, 0, 0);

    // Same projection as the project's camera (gl-matrix perspective with its fovy of 45), from a little closer.
    var f = 1 / Math.tan(45 / 2), near = 0.1, far = 1000, dist = +cv.getAttribute("data-distance") || 3.5;
    var vp = new Float32Array([f, 0, 0, 0, 0, f, 0, 0, 0, 0, (far + near) / (near - far), -1, 0, 0, 0, 0]);
    vp[14] = 2 * far * near / (near - far) - dist * vp[10]; vp[15] = dist;   // projection x translate(0, 0, -dist)

    var size = function () {
      var d = Math.min(window.devicePixelRatio || 1, 2), w = Math.round(cv.clientWidth * d), h = Math.round(cv.clientHeight * d);
      if (w && h && (cv.width !== w || cv.height !== h)) { cv.width = w; cv.height = h; }
      gl.viewport(0, 0, cv.width, cv.height);
      vp[0] = f / (cv.width / cv.height);
      gl.uniformMatrix4fv(U("u_ViewProj"), false, vp);
    };
    var draw = function (ms) {
      size();
      gl.uniform1f(U("u_Time"), 0.5 * ms / 10);                 // timeSpeed 0.5, as in the project
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      gl.drawElements(gl.TRIANGLES, m.idx.length, gl.UNSIGNED_SHORT, 0);
    };

    var seen = true, raf = 0;
    var frame = function (ms) { raf = 0; draw(ms); if (seen && !document.hidden) raf = requestAnimationFrame(frame); };
    var kick = function () { if (!raf && seen && !document.hidden && !still) raf = requestAnimationFrame(frame); };
    draw(still ? 26000 : performance.now());
    box.classList.add("live");
    if (still) { window.addEventListener("resize", function () { draw(26000); }); return; }
    if ("IntersectionObserver" in window) new IntersectionObserver(function (e) { seen = e[0].isIntersecting; kick(); }).observe(cv);
    document.addEventListener("visibilitychange", kick);
    kick();
  }).catch(function () { /* keep the still picture */ });
})();
