// Click a gallery thumbnail to view the full-size image. Without JS the link simply opens the image.
(function () {
  var links = Array.prototype.slice.call(document.querySelectorAll("a.shot"));
  if (!links.length) return;

  var box = document.createElement("div");
  box.className = "lightbox";
  box.setAttribute("role", "dialog");
  box.setAttribute("aria-modal", "true");
  box.setAttribute("aria-label", "Image viewer");
  box.innerHTML =
    '<button class="lb-close" type="button" aria-label="Close">×</button>' +
    '<button class="lb-prev" type="button" aria-label="Previous image">‹</button>' +
    '<img alt="">' +
    '<button class="lb-next" type="button" aria-label="Next image">›</button>' +
    '<p class="lightbox-caption"></p>';
  document.body.appendChild(box);

  var img = box.querySelector("img");
  var cap = box.querySelector(".lightbox-caption");
  var index = 0;
  var opener = null;

  function show(i) {
    index = (i + links.length) % links.length;
    var a = links[index];
    img.src = a.href;
    img.alt = a.querySelector("img").alt || "";
    cap.textContent = a.getAttribute("data-caption") || "";
  }
  function open(i) {
    opener = links[i];
    show(i);
    box.classList.add("open");
    document.documentElement.style.overflow = "hidden";
    box.querySelector(".lb-close").focus();
  }
  function close() {
    box.classList.remove("open");
    document.documentElement.style.overflow = "";
    img.removeAttribute("src");
    if (opener) opener.focus();
  }

  links.forEach(function (a, i) {
    a.addEventListener("click", function (e) {
      if (e.metaKey || e.ctrlKey || e.shiftKey) return;
      e.preventDefault();
      open(i);
    });
  });
  box.querySelector(".lb-close").addEventListener("click", close);
  box.querySelector(".lb-prev").addEventListener("click", function () { show(index - 1); });
  box.querySelector(".lb-next").addEventListener("click", function () { show(index + 1); });
  box.addEventListener("click", function (e) { if (e.target === box) close(); });
  document.addEventListener("keydown", function (e) {
    if (!box.classList.contains("open")) return;
    if (e.key === "Escape") close();
    else if (e.key === "ArrowLeft") show(index - 1);
    else if (e.key === "ArrowRight") show(index + 1);
  });
})();
