/* Home page motion.
   1. The opening: frames of the Virtual Subway scene take turns, each held for a few seconds while it moves slowly
      (the movement itself is in site.css). Frames after the first load only once the page has loaded, and the
      sequence waits while the opening is off screen or the tab is hidden.
   2. Scrolling: the opening falls behind the page (--p, 0 at the top to 1 once it has scrolled away).
   3. Work covers start as a noisy, unconverged render and settle into the finished picture as they come into view.
   With "reduce motion" asked for, the first frame stays still and nothing else moves. */
(function () {
  var root = document.documentElement;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  /* 1. the opening */
  var hero = document.querySelector(".hero");
  var frames = Array.prototype.slice.call(document.querySelectorAll(".hero .frame"));
  var HOLD = 7000, FADE = 1900;
  var at = 0, timer = 0, onScreen = true, started = false;

  function fill(frame) {
    Array.prototype.forEach.call(frame.querySelectorAll("[data-srcset]"), function (el) {
      el.srcset = el.getAttribute("data-srcset");
      el.removeAttribute("data-srcset");
    });
  }
  function whenReady(frame, done) {
    fill(frame);
    var img = frame.querySelector("img");
    var go = function () { (img.decode ? img.decode() : Promise.resolve()).then(done, done); };
    if (img.complete && img.naturalWidth) go();
    else img.addEventListener("load", go, { once: true });
  }
  function advance() {
    var cur = frames[at], n = (at + 1) % frames.length, nxt = frames[n];
    whenReady(nxt, function () {
      if (!onScreen || document.hidden) { started = false; return; }
      cur.classList.remove("on");
      cur.classList.add("out");              // stays under the new frame until it has faded in
      nxt.classList.add("on");
      at = n;
      setTimeout(function () { cur.classList.remove("out"); }, FADE + 100);
      fill(frames[(n + 1) % frames.length]); // fetch the one after while this one is shown
      schedule();
    });
  }
  function schedule() {
    clearTimeout(timer);
    started = true;
    timer = setTimeout(advance, HOLD);
  }
  function resume() {
    if (!started && onScreen && !document.hidden && frames.length > 1) schedule();
  }
  if (hero && frames.length > 1) {
    window.addEventListener("load", function () { fill(frames[1]); schedule(); });
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) { clearTimeout(timer); started = false; } else resume();
    });
    if ("IntersectionObserver" in window) {
      new IntersectionObserver(function (e) {
        onScreen = e[0].isIntersecting;
        if (!onScreen) { clearTimeout(timer); started = false; } else resume();
      }).observe(hero);
    }
  }

  /* 2. scrolling past the opening */
  if (hero) {
    var ticking = false;
    var update = function () {
      ticking = false;
      var p = Math.min(1, Math.max(0, window.scrollY / Math.max(1, hero.offsetHeight)));
      hero.style.setProperty("--p", p.toFixed(3));
    };
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  /* 3. work covers converge as they come into view */
  var works = Array.prototype.slice.call(document.querySelectorAll(".work"));
  if (works.length && "IntersectionObserver" in window) {
    root.classList.add("reveal");
    var io = new IntersectionObserver(function (entries) {
      var batch = entries.filter(function (e) { return e.isIntersecting; }).map(function (e) { return e.target; });
      batch.sort(function (a, b) {
        var ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
        return ra.top - rb.top || ra.left - rb.left;
      });
      batch.forEach(function (el, i) {
        el.style.setProperty("--d", Math.min(i, 5) * 110 + "ms");   // left to right, top to bottom
        el.classList.add("in");
        io.unobserve(el);
      });
    }, { rootMargin: "0px 0px -12% 0px", threshold: 0.12 });
    works.forEach(function (el) { io.observe(el); });
  }
})();
