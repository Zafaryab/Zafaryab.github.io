// js/gallery.js
let PHOTOS = [];
let activeCollection = "All";
let activeTag = "All";

function uniqSorted(arr) {
  return Array.from(new Set(arr)).sort((a, b) => a.localeCompare(b));
}

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function pickIcon(tag) {
  const t = (tag || "").toLowerCase();
  if (t.includes("sunset")) return "fa-sun";
  if (t.includes("snow") || t.includes("winter")) return "fa-snowflake";
  if (t.includes("rain")) return "fa-cloud-rain";
  if (t.includes("fall") || t.includes("autumn")) return "fa-leaf";
  if (t.includes("bird")) return "fa-dove";
  if (t.includes("campus")) return "fa-building-columns";
  if (t.includes("sky")) return "fa-cloud";
  if (t.includes("people")) return "fa-people-group";
  return "fa-camera";
}

function inCollection(photo) {
  if (activeCollection === "All") return true;
  return (photo.collections || []).includes(activeCollection);
}

function matches(photo) {
  const okCollection = inCollection(photo);
  const okTag = (activeTag === "All") || (photo.tags || []).includes(activeTag);
  return okCollection && okTag;
}

function renderCollectionSelect() {
  const select = document.getElementById("collectionSelect");
  if (!select) return;

  const allCollections = uniqSorted(PHOTOS.flatMap(p => p.collections || []));
  const options = ["All", ...allCollections];

  select.innerHTML = options
    .map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`)
    .join("");

  select.value = activeCollection;
}

function renderTagSelect() {
  const select = document.getElementById("tagSelect");
  if (!select) return;

  // Tags only from photos in the currently selected collection
  const scoped = PHOTOS.filter(inCollection);
  const tags = uniqSorted(scoped.flatMap(p => p.tags || []));

  const options = ["All", ...tags];

  select.innerHTML = options
    .map(t => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`)
    .join("");

  // If current tag not available anymore, reset it
  if (!options.includes(activeTag)) activeTag = "All";
  select.value = activeTag;

  // Disable tag dropdown if there are no tags
  select.disabled = (options.length <= 1);
}

function renderGrid() {
  const grid = document.getElementById("galleryGrid");
  const meta = document.getElementById("galleryMeta");
  if (!grid || !meta) return;

  const items = PHOTOS.filter(matches);

  grid.innerHTML = items.map(p => {
    const badgeLabel = (p.tags && p.tags.length) ? p.tags[0] : (p.collections?.[0] || "photo");
    const thumbSrc = p.thumb || p.full;

    return `
      <a href="${p.full}" data-lightbox="gallery" data-title="${escapeHtml(p.title)}" class="shot">
        <span class="tag-abs">${escapeHtml(badgeLabel)}</span>
        <div class="win">
          <img src="${thumbSrc}" alt="${escapeHtml(p.title)}" loading="lazy"
               onerror="this.onerror=null;this.src='${p.full}';" />
        </div>
        <div class="cap">
          <h3 class="t">${escapeHtml(p.title)}</h3>
          <p class="s">${escapeHtml(p.subtitle || "")}</p>
        </div>
      </a>
    `;
  }).join("");

  const parts = [];
  if (activeCollection !== "All") parts.push(`COL: ${escapeHtml(activeCollection)}`);
  if (activeTag !== "All") parts.push(`TAG: ${escapeHtml(activeTag)}`);

  meta.innerHTML = `<b>${items.length}</b> FRAME${items.length === 1 ? "" : "S"}${parts.length ? " // " + parts.join(" // ") : ""}`;
}

function renderAll() {
  renderCollectionSelect();
  renderTagSelect();
  renderGrid();
}

function wireEvents() {
  const collectionSelect = document.getElementById("collectionSelect");
  const tagSelect = document.getElementById("tagSelect");
  const clearBtn = document.getElementById("clearFiltersBtn");

  collectionSelect?.addEventListener("change", () => {
    activeCollection = collectionSelect.value;
    activeTag = "All";          // reset tag when collection changes
    renderAll();
  });

  tagSelect?.addEventListener("change", () => {
    activeTag = tagSelect.value;
    renderGrid();
  });

  clearBtn?.addEventListener("click", () => {
    activeCollection = "All";
    activeTag = "All";
    renderAll();
  });
}

async function initGallery() {
  const res = await fetch("data/photos.json");
  PHOTOS = await res.json();

  wireEvents();
  renderAll();
}

document.addEventListener("DOMContentLoaded", initGallery);
