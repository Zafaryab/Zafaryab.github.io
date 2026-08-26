// js/gallery.js
let PHOTOS = [];
let COLL_ORDER = [];     // ordered place/trip collections (from collections.json)
let FACETS = {};         // controlled secondary attributes (from tag_facets.json)
let activeCollection = "All";
let activeTag = "All";

function escapeHtml(str) {
  return String(str ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

const prettyTag = t => String(t).charAt(0).toUpperCase() + String(t).slice(1);

// canonical "All" order: by collection order, then within-collection order.
// photos with no primary collection sort last.
function collIndex(p) {
  const i = COLL_ORDER.indexOf(p.primary_collection);
  return i === -1 ? Number.MAX_SAFE_INTEGER : i;
}

function inCollection(photo) {
  if (activeCollection === "All") return true;
  return photo.primary_collection === activeCollection
      || (photo.collections || []).includes(activeCollection);
}

function matches(photo) {
  const okCollection = inCollection(photo);
  const okTag = (activeTag === "All") || (photo.tags || []).includes(activeTag);
  return okCollection && okTag;
}

// COLLECTION dropdown: places/trips in curator order.
function renderCollectionSelect() {
  const select = document.getElementById("collectionSelect");
  if (!select) return;
  const options = ["All", ...COLL_ORDER];
  select.innerHTML = options
    .map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`)
    .join("");
  select.value = activeCollection;
}

// FILTER dropdown: controlled facets as <optgroup>s, only values present in
// the current collection scope — never a wall of chips.
function renderTagSelect() {
  const select = document.getElementById("tagSelect");
  if (!select) return;

  const scoped = PHOTOS.filter(inCollection);
  const present = new Set(scoped.flatMap(p => p.tags || []));

  let html = `<option value="All">All</option>`;
  for (const [facet, tags] of Object.entries(FACETS)) {
    const avail = tags.filter(t => present.has(t));
    if (!avail.length) continue;
    html += `<optgroup label="${escapeHtml(facet)}">`
      + avail.map(t => `<option value="${escapeHtml(t)}">${escapeHtml(prettyTag(t))}</option>`).join("")
      + `</optgroup>`;
  }
  select.innerHTML = html;

  if (activeTag !== "All" && !present.has(activeTag)) activeTag = "All";
  select.value = activeTag;
  select.disabled = (present.size === 0);
}

function renderGrid() {
  const grid = document.getElementById("galleryGrid");
  const meta = document.getElementById("galleryMeta");
  if (!grid || !meta) return;

  const items = PHOTOS.filter(matches);

  grid.innerHTML = items.map(p => {
    const thumbSrc = p.thumb || p.large || p.full;
    const lightSrc = p.large || p.full;   // optimized lightbox image; original is archival
    const num = String(p._num ?? "").padStart(3, "0");
    const title = p.title || "Untitled";
    const loc = p.location || "";

    // compact stacked lightbox caption — only fields that carry data
    const meta2 = [loc, p.date || ""].filter(Boolean).map(escapeHtml).join(" · ");
    let cap = `<span class='lb-fr'>FRAME // ${num}</span>`
            + `<span class='lb-ti'>${escapeHtml(title)}</span>`;
    if (p.subtitle) cap += `<span class='lb-sub'>${escapeHtml(p.subtitle)}</span>`;
    if (meta2)      cap += `<span class='lb-meta'>${meta2}</span>`;

    return `
      <a href="${lightSrc}" data-lightbox="gallery" data-title="${cap}" class="shot">
        <div class="win">
          <img src="${thumbSrc}" alt="${escapeHtml(title)}" loading="lazy"
               onerror="this.onerror=null;this.src='${lightSrc}';" />
          <span class="view">View <span class="arw">↗</span></span>
        </div>
        <div class="cap">
          <div class="cap-t"><span class="idx">${num}</span> / ${escapeHtml(title)}</div>
          ${loc ? `<div class="cap-m"><span class="loc">${escapeHtml(loc)}</span></div>` : ""}
        </div>
      </a>
    `;
  }).join("");

  const parts = [];
  if (activeCollection !== "All") parts.push(`COL: ${escapeHtml(activeCollection)}`);
  if (activeTag !== "All") parts.push(`FILTER: ${escapeHtml(prettyTag(activeTag))}`);
  meta.innerHTML = `<b>${items.length}</b> FRAME${items.length === 1 ? "" : "S"}`
    + (parts.length ? " // " + parts.join(" // ") : "");
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
    activeTag = "All";          // reset filter when the place changes
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
  const [photos, colls, facets] = await Promise.all([
    fetch("data/photos.json").then(r => r.json()),
    fetch("data/collections.json").then(r => r.json()),
    fetch("data/tag_facets.json").then(r => r.json()),
  ]);
  PHOTOS = photos;
  COLL_ORDER = colls.map(c => c.name);
  FACETS = Object.fromEntries(Object.entries(facets).filter(([k]) => !k.startsWith("_")));

  // canonical "All" ordering keeps every trip's photos adjacent
  PHOTOS.forEach((p, i) => { p._i = i; });
  PHOTOS.sort((a, b) =>
    (collIndex(a) - collIndex(b))
    || ((a.order ?? 0) - (b.order ?? 0))
    || (a._i - b._i)
  );
  PHOTOS.forEach((p, i) => { p._num = i + 1; });   // stable frame number in All order

  wireEvents();
  renderAll();
}

document.addEventListener("DOMContentLoaded", initGallery);
