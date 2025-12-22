// js/site.js
document.addEventListener("DOMContentLoaded", () => {
  const footer = document.getElementById("footer-placeholder");
  if (!footer) return;

  fetch("partials/footer.html")
    .then(res => res.text())
    .then(html => { footer.innerHTML = html; })
    .catch(() => {
      footer.innerHTML = "<div class='container py-4 text-center text-muted'>Footer failed to load.</div>";
    });
});
