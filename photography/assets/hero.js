/* Opening slideshow on the index page. Without JavaScript only the first
   picture shows. Later pictures are fetched one ahead, not all at once. */
(function () {
  "use strict";
  var hero = document.querySelector(".hero");
  if (!hero) return;
  var slides = Array.prototype.slice.call(hero.querySelectorAll(".slide"));
  var dots = Array.prototype.slice.call(hero.querySelectorAll(".dot"));
  var pause = hero.querySelector(".hero-pause");
  if (slides.length < 2) { if (pause) pause.parentNode.hidden = true; return; }

  var at = 0, want = 0, timer = null, paused = false;
  var still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function load(i) {
    Array.prototype.forEach.call(slides[i].querySelectorAll("[data-srcset]"), function (n) {
      n.srcset = n.getAttribute("data-srcset"); n.removeAttribute("data-srcset");
    });
    var img = slides[i].querySelector("img[data-src]");
    if (img) { img.src = img.getAttribute("data-src"); img.removeAttribute("data-src"); }
  }

  function show(i) {
    i = (i + slides.length) % slides.length;
    if (i === at) return;
    want = i; load(i);
    var img = slides[i].querySelector("img");
    var go = function () {
      if (want !== i) return;
      slides[at].classList.remove("on"); slides[at].setAttribute("aria-hidden", "true"); slides[at].tabIndex = -1;
      dots[at].removeAttribute("aria-current");
      at = i;
      slides[at].classList.add("on"); slides[at].removeAttribute("aria-hidden"); slides[at].tabIndex = 0;
      dots[at].setAttribute("aria-current", "true");
      load((at + 1) % slides.length);
    };
    if (img.complete && img.naturalWidth) go();
    else { img.addEventListener("load", go, { once: true }); img.addEventListener("error", go, { once: true }); }
  }

  function stop() { clearInterval(timer); timer = null; }
  function play() {
    stop();
    if (!paused && !still && !document.hidden) timer = setInterval(function () { show(at + 1); }, 6000);
  }

  dots.forEach(function (d, i) { d.addEventListener("click", function () { show(i); play(); }); });
  pause.addEventListener("click", function () {
    paused = !paused;
    pause.setAttribute("aria-pressed", String(paused));
    pause.setAttribute("aria-label", paused ? "Play slideshow" : "Pause slideshow");
    play();
  });
  document.addEventListener("visibilitychange", play);
  if (still) pause.hidden = true;   // nothing moves on its own; the bars still switch pictures
  load(1); play();
})();
