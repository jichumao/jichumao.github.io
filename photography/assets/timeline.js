/* The timeline page: on wide screens the map stays beside the list, and its points fill in up to
   the series in the middle of the screen, which is marked in red. Elsewhere every point is filled. */
(function () {
  var stops = Array.prototype.slice.call(document.querySelectorAll(".stop"));
  var pins = Array.prototype.slice.call(document.querySelectorAll(".pin"));
  var now = document.querySelector(".tl-now");
  if (!stops.length || !("IntersectionObserver" in window)) return;
  var order = stops.map(function (s) { return s.getAttribute("data-s"); });
  var wide = window.matchMedia("(min-width: 1000px)");
  var cur = -1;

  function paint() {
    var follow = wide.matches;
    pins.forEach(function (p) {
      var i = order.indexOf(p.getAttribute("data-s"));
      p.classList.toggle("seen", !follow || i <= cur);
      p.classList.toggle("on", follow && i === cur);
    });
    stops.forEach(function (s, i) {
      s.classList.toggle("on", follow && i === cur);
    });
    if (now) {
      now.firstChild.textContent = cur < 0 ? "" : stops[cur].getAttribute("data-title");
      now.lastChild.textContent = cur < 0 ? now.getAttribute("data-idle") : stops[cur].getAttribute("data-meta");
    }
  }

  // The series whose block crosses the middle of the screen is the current one.
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      var i = stops.indexOf(e.target);
      if (e.isIntersecting) cur = i;
      else if (i === 0 && e.boundingClientRect.top > window.innerHeight / 2) cur = -1;
    });
    paint();
  }, { rootMargin: "-48% 0px -48% 0px" });
  stops.forEach(function (s) { io.observe(s); });

  // The last series may never reach the middle of the screen: at the foot of the page it is current.
  window.addEventListener("scroll", function () {
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 4 && cur !== stops.length - 1) {
      cur = stops.length - 1; paint();
    }
  }, { passive: true });

  if (wide.addEventListener) wide.addEventListener("change", paint); else wide.addListener(paint);
  document.documentElement.classList.add("tl-js");
  paint();
})();
