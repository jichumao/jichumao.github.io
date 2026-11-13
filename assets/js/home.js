/* Home page motion (the opening itself is assets/js/cornell.js).
   1. Scrolling: the opening falls behind the page (--p, 0 at the top to 1 once it has scrolled away).
   2. Work covers start as a noisy, unconverged render and settle into the finished picture as they come into view.
   With "reduce motion" asked for, nothing moves. */
(function () {
  var root = document.documentElement;
  if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

  var hero = document.querySelector(".hero");

  /* 1. scrolling past the opening */
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

  /* 2. work covers converge as they come into view */
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
