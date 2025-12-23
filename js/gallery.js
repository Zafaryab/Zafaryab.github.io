// js/gallery.js
let PHOTOS = [];
let activeCollection = "All";
let activeCategory = "all";
let activeTag = "all";

const CATEGORY_LABELS = {
  all: "All",
  birds: "Birds",
  landscapes: "Landscapes",
  people: "People / Groups"
};

function uniqSorted(arr) {
  return Array.from(new Set(arr)).sort((a, b) => a.localeCompare(b));
}

function matches(photo) {
  const okCollection = (activeCollection === "All") || (photo.collections || []).includes(activeCollection);
  const okCategory = (activeCategory === "all") || (photo.category === activeCategory);
  const okTag = (activeTag === "all") || (photo.tags || []).includes(activeTag);
  return okCollection && okCategory && okTag;
}

function renderCollections() {
  const allCollections = uniqSorted(PHOTOS.flatMap(p => p.collections || []));
  const collections = ["All", ...allCollections];

  const row = document.getElementById("collectionsRow");
  row.innerHTML = collections.map(name => {
    const count = PHOTOS.filter(p => (name === "All") ? true : (p.collections || []).includes(name)).length;
    const isActive = name === activeCollection;

    return `
      <div class="col-12 col-sm-6 col-lg-3">
        <button type="button"
          class="collection-card ${isActive ? "is-active" : ""}"
          data-collection="${escapeHtml(name)}">
          <div class="d-flex align-items-start justify-content-between gap-2">
            <div>
              <div class="fw-bold">${escapeHtml(name)}</div>
              <div class="collection-muted">${count} photo${count === 1 ? "" : "s"}</div>
            </div>
            <div class="collection-icon"><i class="fa-solid fa-layer-group"></i></div>
          </div>
        </button>
      </div>
    `;
  }).join("");

  row.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-collection]");
    if (!btn) return;
    activeCollection = btn.dataset.collection;
    renderAll();
  }, { once: true });
}

function renderCategories() {
  const cats = uniqSorted(PHOTOS.map(p => p.category));
  const buttons = ["all", ...cats];

  const wrap = document.getElementById("categoryFilters");
  wrap.innerHTML = buttons.map(c => {
    const label = CATEGORY_LABELS[c] || (c.charAt(0).toUpperCase() + c.slice(1));
    const active = c === activeCategory ? "active" : "";
    return `
      <button type="button" class="btn btn-outline-dark btn-sm ${active}" data-category="${c}">
        ${escapeHtml(label)}
      </button>
    `;
  }).join("");

  wrap.onclick = (e) => {
    const btn = e.target.closest("[data-category]");
    if (!btn) return;
    activeCategory = btn.dataset.category;
    renderAll();
  };
}

function renderTags() {
  const tags = uniqSorted(PHOTOS.flatMap(p => p.tags || []));
  const list = ["all", ...tags];

  const wrap = document.getElementById("tagFilters");
  wrap.innerHTML = list.map(t => {
    const label = t === "all" ? "All" : t.replace(/-/g, " ");
    const active = t === activeTag ? "is-active" : "";
    return `
      <button type="button" class="tag-pill ${active}" data-tag="${t}">
        <i class="fa-solid fa-tag me-2"></i>${escapeHtml(label)}
      </button>
    `;
  }).join("");

  wrap.onclick = (e) => {
    const btn = e.target.closest("[data-tag]");
    if (!btn) return;
    activeTag = btn.dataset.tag;
    renderAll();
  };
}

function renderGrid() {
  const grid = document.getElementById("galleryGrid");
  const meta = document.getElementById("galleryMeta");

  const items = PHOTOS.filter(matches);

  grid.innerHTML = items.map(p => {
    const tagLabel = (p.tags && p.tags.length) ? p.tags[0] : p.category;
    const icon = pickIcon(tagLabel);

    return `
      <div class="col-12 col-sm-6 col-lg-4">
        <a href="${p.full}" data-lightbox="gallery" data-title="${escapeHtml(p.title)}" class="text-decoration-none">
          <article class="gallery-card">
            <div class="tag"><i class="fa-solid ${icon} me-1"></i> ${escapeHtml(tagLabel)}</div>
            <div class="photo-window">
              <img src="${p.thumb}" alt="${escapeHtml(p.title)}" loading="lazy" />
            </div>
            <div class="caption">
              <h3 class="h6 title">${escapeHtml(p.title)}</h3>
              <p class="sub">${escapeHtml(p.subtitle || "")}</p>
            </div>
          </article>
        </a>
      </div>
    `;
  }).join("");

  const parts = [];
  if (activeCollection !== "All") parts.push(`Collection: <strong>${escapeHtml(activeCollection)}</strong>`);
  if (activeCategory !== "all") parts.push(`Category: <strong>${escapeHtml(activeCategory)}</strong>`);
  if (activeTag !== "all") parts.push(`Tag: <strong>${escapeHtml(activeTag)}</strong>`);
  const filterText = parts.length ? ` · ${parts.join(" · ")}` : "";

  meta.innerHTML = `<span class="fw-semibold">${items.length}</span> photo${items.length === 1 ? "" : "s"} shown${filterText}`;
}

function renderAll() {
  // re-render collections so active state updates
  renderCollections();
  renderCategories();
  renderTags();
  renderGrid();
  wireClearButton();
}

function wireClearButton() {
  const btn = document.getElementById("clearFiltersBtn");
  btn.onclick = () => {
    activeCollection = "All";
    activeCategory = "all";
    activeTag = "all";
    renderAll();
  };
}

function pickIcon(tag) {
  const t = (tag || "").toLowerCase();
  if (t.includes("sunset")) return "fa-sun";
  if (t.includes("snow") || t.includes("winter")) return "fa-snowflake";
  if (t.includes("rain")) return "fa-cloud-rain";
  if (t.includes("fall") || t.includes("autumn")) return "fa-leaf";
  if (t.includes("bird")) return "fa-dove";
  if (t.includes("street") || t.includes("people")) return "fa-city";
  return "fa-camera";
}

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function initGallery() {
  const res = await fetch("data/photos.json");
  PHOTOS = await res.json();
  renderAll();
}

document.addEventListener("DOMContentLoaded", initGallery);
