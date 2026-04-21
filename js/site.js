// js/site.js
// Loads the shared header and footer partials and highlights the active nav item.
async function loadPartial(selector, path) {
  const el = document.querySelector(selector);
  if (!el) return;
  try {
    const res = await fetch(path);
    if (!res.ok) throw new Error(res.statusText);
    el.innerHTML = await res.text();
  } catch {
    el.innerHTML = "<div class='container py-4 text-center text-muted'>Section failed to load.</div>";
  }
}

function setActiveNav() {
  const file = (location.pathname.split("/").pop() || "index.html").toLowerCase();
  document.querySelectorAll("[data-nav]").forEach((a) => {
    const target = (a.getAttribute("data-nav") || "").toLowerCase();
    if (target === file) {
      a.classList.add("active");
      a.setAttribute("aria-current", "page");
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  await Promise.all([
    loadPartial("#header-placeholder", "partials/header.html"),
    loadPartial("#footer-placeholder", "partials/footer.html"),
  ]);
  setActiveNav();
});
