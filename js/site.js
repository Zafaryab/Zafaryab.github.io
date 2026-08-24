// js/site.js
// Loads the shared header/footer partials, highlights the active nav item,
// and wires the compact mobile navigation toggle.
async function loadPartial(selector, path) {
  const el = document.querySelector(selector);
  if (!el) return;
  try {
    const res = await fetch(path);
    if (!res.ok) throw new Error(res.statusText);
    el.innerHTML = await res.text();
  } catch {
    el.innerHTML = "<div class='wrap' style='padding:1rem 0;color:var(--text-muted);font-family:var(--mono)'>// section failed to load</div>";
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

function wireNavToggle() {
  const btn = document.querySelector(".nav-toggle");
  const nav = document.querySelector("#primary-nav");
  if (!btn || !nav) return;
  btn.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    btn.textContent = open ? "[ CLOSE ]" : "[ MENU ]";
  });
  // close the menu after choosing a destination
  nav.querySelectorAll("a").forEach((a) =>
    a.addEventListener("click", () => {
      nav.classList.remove("open");
      btn.setAttribute("aria-expanded", "false");
      btn.textContent = "[ MENU ]";
    })
  );
}

document.addEventListener("DOMContentLoaded", async () => {
  await Promise.all([
    loadPartial("#header-placeholder", "partials/header.html"),
    loadPartial("#footer-placeholder", "partials/footer.html"),
  ]);
  setActiveNav();
  wireNavToggle();
});
