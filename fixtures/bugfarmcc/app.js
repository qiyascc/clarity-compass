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

console.error("analytics: failed to initialise tracker");
