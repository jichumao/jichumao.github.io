// Card previews: a cover plays a short silent loop while its card sits in the middle of the
// screen, so one row of the grid is in motion at a time. Hovering or focusing a card plays it
// too. Nothing is downloaded until a preview is first needed. Off with reduced motion or data saver.
(function () {
  var cards = Array.prototype.slice.call(document.querySelectorAll(".work"));
  if (!cards.length || !window.matchMedia) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (navigator.connection && navigator.connection.saveData) return;
  document.documentElement.classList.add("previews");

  function update(card) {
    var v = card.querySelector(".work-preview");
    if (!v) return;
    var want = card._band || card._hover;
    if (want && !card._on) {
      card._on = true;
      if (!v.getAttribute("src")) v.src = v.getAttribute("data-src");
      var show = function () { if (card._on) card.classList.add("playing"); };
      var p = v.play();
      if (p && p.then) p.then(show, function () {}); else show();
    } else if (!want && card._on) {
      card._on = false;
      card.classList.remove("playing");
      v.pause();
      setTimeout(function () { if (!card._on) { try { v.currentTime = 0; } catch (e) {} } }, 400);
    }
  }

  cards.forEach(function (c) {
    c.addEventListener("pointerenter", function (e) { if (e.pointerType !== "touch") { c._hover = true; update(c); } });
    c.addEventListener("pointerleave", function () { c._hover = false; update(c); });
    c.addEventListener("focusin", function () { c._hover = true; update(c); });
    c.addEventListener("focusout", function () { c._hover = false; update(c); });
  });

  if ("IntersectionObserver" in window) {
    // the observed band is the middle 30% of the viewport
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var card = e.target.parentNode;
        card._band = e.isIntersecting;
        update(card);
      });
    }, { rootMargin: "-35% 0px -35% 0px" });
    cards.forEach(function (c) { io.observe(c.querySelector(".work-frame")); });
  }
})();
