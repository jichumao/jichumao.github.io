// Home page: filter the "More work" grid by category. Without JS the filter bar stays hidden and every project shows.
(function () {
  var bar = document.querySelector(".work-filter");
  if (!bar) return;
  var buttons = Array.prototype.slice.call(bar.querySelectorAll("button"));
  var items = Array.prototype.slice.call(document.querySelectorAll(".work.mini"));
  bar.hidden = false;
  bar.addEventListener("click", function (e) {
    var b = e.target.closest ? e.target.closest("button") : null;
    if (!b) return;
    var cat = b.getAttribute("data-cat");
    buttons.forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
    items.forEach(function (li) {
      var cats = " " + (li.getAttribute("data-cats") || "") + " ";
      li.hidden = !(cat === "all" || cats.indexOf(" " + cat + " ") >= 0);
    });
  });
})();
