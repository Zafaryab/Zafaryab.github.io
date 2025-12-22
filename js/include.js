// js/includes.js
async function loadPartial(selector, path) {
  const el = document.querySelector(selector);
  if (!el) return;
  const res = await fetch(path);
  el.innerHTML = await res.text();
}

function setActiveNav() {
  const file = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll("[data-nav]").forEach((a) => {
    if (a.getAttribute("data-nav") === file) a.classList.add("active");
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  await loadPartial("#header-placeholder", "partials/header.html");
  await loadPartial("#footer-placeholder", "partials/footer.html");
  setActiveNav();
});
