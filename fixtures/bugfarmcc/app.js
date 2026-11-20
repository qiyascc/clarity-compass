const lazy = document.getElementById("lazy-more");

new IntersectionObserver((entries, observer) => {
  if (!entries.some((entry) => entry.isIntersecting)) return;
  observer.disconnect();
  setTimeout(() => {
    lazy.innerHTML = '<h2 id="late-heading">More homes</h2><div style="height:900px"></div>';
  }, 300);
}).observe(lazy);

document.getElementById("lang").addEventListener("click", () => {
  document.getElementById("lang").textContent = "AZ";
});

document.getElementById("to-top").addEventListener("click", () => {
  window.scrollToTop();
});

const filters = document.getElementById("filters");
filters.addEventListener("click", () => {
  filters.setAttribute("aria-expanded", "true");
  document.getElementById("filter-panel").hidden = false;
});

document.getElementById("newsletter").addEventListener("click", () => {
  const dialog = document.createElement("div");
  dialog.setAttribute("role", "dialog");
  dialog.style.cssText = "position:fixed;inset:20%;background:#fff;border:1px solid #ccc;padding:24px";
  dialog.textContent = "Subscribe to new listings";
  document.body.append(dialog);
});

console.error("analytics: failed to initialise tracker");
