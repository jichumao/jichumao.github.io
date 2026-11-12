/* Full-screen viewer for a series page. Works on the links the page already
   has (a.ph[data-w]); without JavaScript those links open the large file. */
(function () {
  "use strict";
  var links = Array.prototype.slice.call(document.querySelectorAll("a.ph[data-w]"));
  if (!links.length) return;

  var title = document.body.getAttribute("data-series") || "";
  var svg = function (d) { return '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="' + d + '"/></svg>'; };
  var el = document.createElement("div");
  el.className = "viewer"; el.hidden = true;
  el.setAttribute("role", "dialog"); el.setAttribute("aria-modal", "true"); el.setAttribute("aria-label", "Photo viewer");
  el.innerHTML =
    '<div class="v-stage">' +
    '<button class="v-btn v-close" type="button" aria-label="Close viewer">' + svg("M6 6l12 12M18 6L6 18") + "</button>" +
    '<button class="v-btn v-prev" type="button" aria-label="Previous photograph">' + svg("M15 5l-7 7 7 7") + "</button>" +
    '<img class="v-img" alt="">' +
    '<button class="v-btn v-next" type="button" aria-label="Next photograph">' + svg("M9 5l7 7-7 7") + "</button>" +
    '</div><p class="v-cap" aria-live="polite"><span><b class="v-title"></b> <span class="v-count"></span><span class="v-place"></span></span><span class="v-set"></span></p>';
  document.body.appendChild(el);

  var stage = el.querySelector(".v-stage"), img = el.querySelector(".v-img"), cap = el.querySelector(".v-cap");
  var prev = el.querySelector(".v-prev"), next = el.querySelector(".v-next"), close = el.querySelector(".v-close");
  var at = -1, opener = null, pushed = false;

  function fit() {
    if (at < 0) return;
    var a = links[at], w = +a.dataset.w, h = +a.dataset.h;
    var s = Math.min(stage.clientWidth / w, stage.clientHeight / h, 1);
    img.style.width = Math.round(w * s) + "px";
    img.style.height = Math.round(h * s) + "px";
    img.sizes = Math.round(w * s) + "px";
  }

  function warm(i) {
    if (i < 0 || i >= links.length) return;
    var a = links[i], p = new Image();
    var s = Math.min(stage.clientWidth / +a.dataset.w, stage.clientHeight / +a.dataset.h, 1);
    p.sizes = Math.round(+a.dataset.w * s) + "px";
    p.srcset = a.dataset.srcset;
  }

  function show(i) {
    at = i;
    var a = links[i], thumb = a.querySelector("img");
    img.removeAttribute("srcset"); img.removeAttribute("src");
    img.style.backgroundColor = a.style.getPropertyValue("--c") || "#111";
    img.style.backgroundImage = thumb && thumb.currentSrc ? 'url("' + thumb.currentSrc + '")' : "none";
    img.alt = thumb ? thumb.alt : "";
    fit();
    img.srcset = a.dataset.srcset;
    img.src = a.href;
    el.querySelector(".v-title").textContent = title;
    el.querySelector(".v-count").textContent = (i + 1) + " / " + links.length;
    el.querySelector(".v-place").textContent = a.dataset.cap || "";
    el.querySelector(".v-set").textContent = a.dataset.settings || "";
    prev.disabled = i === 0; next.disabled = i === links.length - 1;
    history.replaceState(history.state, "", "#" + (i + 1));
    warm(i + 1); warm(i - 1);
  }

  function open(i, push) {
    opener = document.activeElement;
    el.hidden = false; document.documentElement.classList.add("viewing");
    if (push) { history.pushState({ viewer: true }, "", "#" + (i + 1)); pushed = true; }
    show(i); close.focus();
  }

  function shut(fromPop) {
    if (el.hidden) return;
    el.hidden = true; document.documentElement.classList.remove("viewing");
    var a = links[at]; at = -1;
    if (pushed && !fromPop) { pushed = false; history.back(); }
    else { pushed = false; history.replaceState(null, "", location.pathname + location.search); }
    if (a) { a.scrollIntoView({ block: "nearest" }); a.focus({ preventScroll: true }); }
    else if (opener && opener.focus) opener.focus();
  }

  function step(d) { var i = at + d; if (i >= 0 && i < links.length) show(i); }

  links.forEach(function (a, i) {
    a.addEventListener("click", function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button) return;
      e.preventDefault(); open(i, true);
    });
  });
  prev.addEventListener("click", function (e) { e.stopPropagation(); step(-1); });
  next.addEventListener("click", function (e) { e.stopPropagation(); step(1); });
  close.addEventListener("click", function (e) { e.stopPropagation(); shut(); });
  img.addEventListener("click", function (e) { e.stopPropagation(); if (at < links.length - 1) step(1); });
  stage.addEventListener("click", function () { shut(); });
  window.addEventListener("popstate", function () { shut(true); });
  window.addEventListener("resize", fit);

  document.addEventListener("keydown", function (e) {
    if (el.hidden) return;
    if (e.key === "Escape") { e.preventDefault(); shut(); }
    else if (e.key === "ArrowRight" || e.key === " ") { e.preventDefault(); step(1); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); step(-1); }
    else if (e.key === "Home") { e.preventDefault(); show(0); }
    else if (e.key === "End") { e.preventDefault(); show(links.length - 1); }
    else if (e.key === "Tab") {
      var f = [close, prev, next].filter(function (b) { return !b.disabled && b.offsetParent; });
      var k = f.indexOf(document.activeElement);
      e.preventDefault();
      f[(k + (e.shiftKey ? f.length - 1 : 1)) % f.length].focus();
    }
  });

  var x0 = null, y0 = 0;
  stage.addEventListener("touchstart", function (e) {
    if (e.touches.length === 1) { x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; } else x0 = null;
  }, { passive: true });
  stage.addEventListener("touchend", function (e) {
    if (x0 === null) return;
    var t = e.changedTouches[0], dx = t.clientX - x0, dy = t.clientY - y0; x0 = null;
    if (Math.abs(dx) > 48 && Math.abs(dx) > Math.abs(dy) * 1.4) step(dx < 0 ? 1 : -1);
    else if (dy > 90 && Math.abs(dy) > Math.abs(dx) * 1.4) shut();
  }, { passive: true });

  var m = /^#(\d+)$/.exec(location.hash);
  if (m && +m[1] >= 1 && +m[1] <= links.length) open(+m[1] - 1, false);
})();
