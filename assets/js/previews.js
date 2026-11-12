// Card previews: the main panel of a cover plays a short silent loop while the card is
// hovered or focused. On touch screens the card crossing the middle of the screen plays.
// Nothing is downloaded until a preview is first needed. Off with reduced motion or data saver.
(function () {
  var cards = Array.prototype.slice.call(document.querySelectorAll(".work"));
  if (!cards.length || !window.matchMedia) return;
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  if (navigator.connection && navigator.connection.saveData) return;
  document.documentElement.classList.add("previews");
  var current = null;

  function stop(card) {
    var v = card.querySelector(".work-preview");
    card.classList.remove("playing");
    if (current === card) current = null;
    if (!v) return;
    v.pause();
    setTimeout(function () { if (current !== card) { try { v.currentTime = 0; } catch (e) {} } }, 400);
  }

  function start(card) {
    if (current === card) return;
    if (current) stop(current);
    var v = card.querySelector(".work-preview");
    if (!v) return;
    if (!v.getAttribute("src")) v.src = v.getAttribute("data-src");
    current = card;
    var show = function () { if (current === card) card.classList.add("playing"); };
    var p = v.play();
    if (p && p.then) p.then(show, function () {}); else show();
  }

  if (window.matchMedia("(hover: hover)").matches) {
    cards.forEach(function (c) {
      c.addEventListener("pointerenter", function () { start(c); });
      c.addEventListener("pointerleave", function () { stop(c); });
      c.addEventListener("focusin", function () { start(c); });
      c.addEventListener("focusout", function () { stop(c); });
    });
  } else if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        var card = e.target.parentNode;
        if (e.isIntersecting) start(card); else if (current === card) stop(card);
      });
    }, { rootMargin: "-40% 0px -40% 0px" });
    cards.forEach(function (c) { io.observe(c.querySelector(".work-frame")); });
  }
})();
