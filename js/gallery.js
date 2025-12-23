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
  if (!row) return;
  row.innerHTML = collections.map(name => {
    const active = (name === activeCollection) ? "is-active" : "";
    return `<button type="button" class="filter-pill ${active}" data-collection="${escapeHtml(name)}">${escapeHtml(name)}</button>`;
  }).join("");

  row.onclick = (e) => {
    const btn = e.target.closest("[data-collection]");
    if (!btn) return;
    activeCollection = btn.dataset.collection;
    renderAll();
  };
}


function renderTags() {
  const tags = uniqSorted(PHOTOS.flatMap(p => p.tags || []));
  const limited = tags.slice(0, 10); // show max 10 tags
  const list = ["all", ...limited];

  const wrap = document.getElementById("tagFilters");
  if (!wrap) return;
  wrap.innerHTML = list.map(t => {
    const label = t === "all" ? "All" : t.replace(/-/g, " ");
    const active = t === activeTag ? "is-active" : "";
    return `<button type="button" class="tag-pill ${active}" data-tag="${t}">${escapeHtml(label)}</button>`;
  }).join("");

  wrap.onclick = (e) => {
    const btn = e.target.closest("[data-tag]");
    if (!btn) return;
    activeTag = btn.dataset.tag;
    renderAll();
  };
}

function renderCategories() {
  const wrap = document.getElementById("categoryFilters");
  if (!wrap) return;

  const cats = uniqSorted(PHOTOS.map(p => p.category).filter(Boolean));
  const buttons = ["all", ...cats];

  wrap.innerHTML = buttons.map(c => {
    const label = CATEGORY_LABELS[c] || (c.charAt(0).toUpperCase() + c.slice(1));
    const active = (c === activeCategory) ? "active" : "";
    return `<button type="button" class="btn btn-outline-dark btn-sm ${active}" data-category="${c}">${escapeHtml(label)}</button>`;
  }).join("");

  wrap.onclick = (e) => {
    const btn = e.target.closest("[data-category]");
    if (!btn) return;
    activeCategory = btn.dataset.category;
    renderAll();
  };
}


function renderGrid() {
  const grid = document.getElementById("galleryGrid");
  const meta = document.getElementById("galleryMeta");
  if (!grid || !meta) return;

  const items = PHOTOS.filter(matches);

  grid.innerHTML = items.map(p => {
    const tagLabel = (p.tags && p.tags.length) ? p.tags[0] : p.category;
    const icon = pickIcon(tagLabel);
    const thumbSrc = p.thumb || p.full;

    return `
      <div class="col-12 col-sm-6 col-lg-4">
        <a href="${p.full}" data-lightbox="gallery" data-title="${escapeHtml(p.title)}" class="text-decoration-none">
          <article class="gallery-card">
            <div class="tag"><i class="fa-solid ${icon} me-1"></i> ${escapeHtml(tagLabel)}</div>
            <div class="photo-window">
              <img src="${thumbSrc}" alt="${escapeHtml(p.title)}" loading="lazy" onerror="this.onerror=null;this.src='${p.full}';" />
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
