// Short looping demo clips (converted from GIFs): play while on screen, pause when scrolled away.
// With reduced motion, or without IntersectionObserver, they stay as ordinary videos with controls.
(function () {
  var vids = Array.prototype.slice.call(document.querySelectorAll("video[data-autoplay]"));
  if (!vids.length) return;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce || !("IntersectionObserver" in window)) return;
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      var v = e.target;
      if (e.isIntersecting) {
        var p = v.play();
        if (p && p.catch) p.catch(function () { if (!v.classList.contains("work-preview")) v.controls = true; });
      } else {
        v.pause();
      }
    });
  }, { threshold: 0.25 });
  vids.forEach(function (v) {
    v.controls = false;
    // the preview over a project page's cover fades in once it is actually playing
    v.addEventListener("playing", function () { v.classList.add("on"); });
    io.observe(v);
  });
})();
