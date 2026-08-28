#!/usr/bin/env python3
"""
build_research.py — generate static research HTML from the canonical data.

data/research.json is the single source of truth for publications, patents,
current research, research-focus areas and the homepage counters. This script
renders those into plain static HTML between <!-- build:NAME:start/end -->
markers in index.html and resume.html, so the deployed pages stay ordinary
static HTML (no client-side fetch / JS dependency for content).

Usage
    python scripts/build_research.py          # regenerate the marked sections
    python scripts/build_research.py --check    # validate data + flag stale HTML
                                                # (exit 1 on any problem)

Never hand-edit content between the build markers — edit research.json and rerun.
"""

from __future__ import annotations

import argparse
import html as _html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "research.json"
INDEX = ROOT / "index.html"
RESUME = ROOT / "resume.html"

STATUS_CLASS = {
    "active": "active", "upcoming": "upcoming",
    "published": "pub", "accepted": "accepted", "under_review": "submitted",
    "filed": "pub",
}
STATUS_LABEL = {"published": "Published", "accepted": "Accepted", "under_review": "Under Review"}
PUB_GROUPS = [("published", "Published", ""), ("accepted", "Accepted", " magenta"),
              ("under_review", "Under Review", " amber")]


# ---------------------------------------------------------------- helpers
def esc(s) -> str:
    return _html.escape(str(s), quote=False)


def authors_html(authors: str, me: str) -> str:
    e, em = esc(authors), esc(me)
    return e.replace(em, f'<span class="me">{em}</span>', 1)


def links_html(links) -> str:
    out = ""
    for l in links or []:
        out += (f'\n      <a class="link-u" href="{esc(l["href"])}" '
                f'target="_blank" rel="noopener">{esc(l["label"])} ↗</a>')
    return out


# ---------------------------------------------------------------- renderers
def render_focus(d) -> str:
    return "\n".join(
        f'<div class="sys-row"><span class="k">{esc(f["n"])}</span>'
        f'<span class="v">{esc(f["label"])}</span>'
        f'<span class="s {esc(f["accent"])}">{esc(f["anchor"])}</span></div>'
        for f in d["focus"]
    )


def counts(d) -> dict:
    p = d["publications"]
    return {
        "published_accepted": len(p["published"]) + len(p["accepted"]),
        "under_review": len(p["under_review"]),
        "patents": len(d["patents"]),
    }


def render_counters(d) -> str:
    c = counts(d)
    rows = []
    for item in d["counters"]:
        value = f'{c[item["source"]]:02d}' if "source" in item else item["value"]
        amber = " amber" if item.get("accent") == "amber" else ""
        rows.append(f'<div class="dash-stat{amber}"><b>{esc(value)}</b>'
                    f'<span>{esc(item["label"])}</span></div>')
    return "\n".join(rows)


def render_current(d) -> str:
    cells = []
    for p in d["current"]:
        meta = ""
        for k, v, vc in p["meta"]:
            cls = f' class="{vc}"' if vc else ""
            meta += (f'\n      <span class="kv"><b>{esc(k)}</b>'
                     f'<span{cls}>{esc(v)}</span></span>')
        cells.append(
            f'<div class="proj proj-lead">\n'
            f'  <div class="proj-top"><span class="proj-id"><span class="n">{esc(p["n"])}</span>'
            f'{esc(p["id"])}</span>'
            f'<span class="status status--{STATUS_CLASS[p["status"]]}">{esc(p["status_label"])}</span></div>\n'
            f'  <div class="proj-cat">{esc(p["cat"])}</div>\n'
            f'  <div class="proj-meta">{meta}\n  </div>\n'
            f'  <p class="proj-desc">{esc(p["desc"])}</p>\n'
            f'</div>'
        )
    return "\n\n".join(cells)


def _pub_article(p) -> str:
    body = f'      <h4 class="pub-title">{esc(p["title"])}</h4>\n'
    body += f'      <div class="pub-authors">{authors_html(p["authors"], p["me"])}</div>\n'
    body += f'      <div class="pub-tags">{esc(p["tags"])}</div>'
    if p.get("contribution"):
        body += (f'\n      <p class="pub-contrib"><span class="k">Contribution</span>'
                 f'{esc(p["contribution"])}</p>')
    if p.get("note"):
        n = p["note"]
        if n.get("hidden"):
            # preserved in the source as an HTML comment, but not shown
            safe = f'{n["k"]} {n["text"]}'.replace("--", "—")
            body += f'\n      <!-- {safe} -->'
        else:
            body += (f'\n      <p class="pub-note"><span class="k">{esc(n["k"])}</span> '
                     f'{esc(n["text"])}</p>')
    aside = f'<span class="status status--{STATUS_CLASS[p["status"]]}">{STATUS_LABEL[p["status"]]}</span>'
    aside += links_html(p.get("links"))
    year = p.get("year") or "—"
    # under-review work hides its target venue (kept in source as a comment) —
    # naming a venue before acceptance reads as presumptuous
    if p["status"] == "under_review":
        venue_html = f'<!-- target venue: {esc(p["venue"])} -->'
    else:
        venue_html = f'<div class="pub-venue">{esc(p["venue"])}</div>'
    return (
        f'<article class="pub">\n'
        f'  <div class="pub-side"><div class="pub-year">{esc(year)}</div>'
        f'{venue_html}</div>\n'
        f'  <div class="pub-body">\n'
        f'    <div>\n{body}\n    </div>\n'
        f'    <div class="pub-aside">\n      {aside}\n    </div>\n'
        f'  </div>\n'
        f'</article>'
    )


def render_publications(d) -> str:
    parts = []
    for key, label, cls in PUB_GROUPS:
        parts.append(f'<div class="pub-group{cls}">{label}</div>')
        parts.extend(_pub_article(p) for p in d["publications"][key])
    return "\n\n".join(parts)


def render_patents(d) -> str:
    cells = []
    for p in d["patents"]:
        aside = '<span class="status status--pub">Filed</span>' + links_html(p.get("links"))
        cells.append(
            f'<article class="pub">\n'
            f'  <div class="pub-side"><div class="pub-year" style="color:var(--green)">{esc(p["n"])}</div>'
            f'<div class="pub-venue">{esc(p["kind"])}</div></div>\n'
            f'  <div class="pub-body">\n'
            f'    <div>\n'
            f'      <h4 class="pub-title">{esc(p["title"])}</h4>\n'
            f'      <div class="pub-authors">{authors_html(p["inventors"], p["me"])}</div>\n'
            f'      <div class="pub-tags">{esc(p["detail"])}</div>\n'
            f'    </div>\n'
            f'    <div class="pub-aside">\n      {aside}\n    </div>\n'
            f'  </div>\n'
            f'</article>'
        )
    return "\n\n".join(cells)


def _engineering_by_year(d) -> list:
    """Engineering systems newest-first (by year)."""
    return sorted(d["engineering"], key=lambda s: int(str(s["year"])[:4]), reverse=True)


def render_engineering(d) -> str:
    cells = []
    for s in _engineering_by_year(d):
        cells.append(
            f'<div class="proj">\n'
            f'  <div class="proj-top"><span class="proj-id">{esc(s["title"])}</span>'
            f'<span class="tag">{esc(s["year"])}</span></div>\n'
            f'  <div class="proj-cat">{esc(s["cat"])}</div>\n'
            f'  <p class="proj-desc">{esc(s["desc"])}</p>\n'
            f'</div>'
        )
    return "\n\n".join(cells)


# ------------------------------------------------ homepage selected research
def _selected_items(d) -> list:
    """All records flagged for the homepage showcase, in homepage.order.
    Venue / status / year / category are read from the canonical record;
    only order, short code and the showcase summary live under `homepage`."""
    items = [("current", c) for c in d["current"] if "homepage" in c]
    for grp in ("published", "accepted", "under_review"):
        items += [("pub", p) for p in d["publications"][grp] if "homepage" in p]
    items.sort(key=lambda t: t[1]["homepage"]["order"])
    return items


def _selected_card(kind, rec) -> str:
    hp = rec["homepage"]
    num = f'{hp["order"]:02d}'
    if kind == "current":
        name = rec["id"]
        cat = rec["cat"]
        status_label = rec["status"].capitalize()      # Active / Upcoming
        status_cls = STATUS_CLASS[rec["status"]]
        href = "resume.html#current"
        k, v, _ = rec["meta"][0]                        # first meta pair only
        meta_pairs = [(k, v)]
    else:
        name = hp["code"]
        cat = rec["tags"]
        status_label = STATUS_LABEL[rec["status"]]
        status_cls = STATUS_CLASS[rec["status"]]
        href = "resume.html#publications"
        meta_pairs = [("Venue", rec["venue"])]
        if rec.get("year"):
            meta_pairs.append(("Year", rec["year"]))

    lines = [
        f'<a class="proj" href="{href}">',
        f'  <div class="proj-top"><span class="proj-id"><span class="n">{num}</span>'
        f'{esc(name)}</span><span class="status status--{status_cls}">{esc(status_label)}</span></div>',
        f'  <div class="proj-cat">{esc(cat)}</div>',
        f'  <div class="proj-meta">',
    ]
    for k, v in meta_pairs:
        lines.append(f'    <span class="kv"><b>{esc(k)}</b><span class="amber">{esc(v)}</span></span>')
    lines += [
        f'  </div>',
        f'  <p class="proj-desc">{esc(hp["summary"])}</p>',
        f'</a>',
    ]
    return "\n".join(lines)


def render_selected(d) -> str:
    return "\n\n".join(_selected_card(k, r) for k, r in _selected_items(d))


def render_selected_count(d) -> str:
    return f'<span class="tag">{len(_selected_items(d)):02d} SELECTED</span>'


def render_engineering_home(d) -> str:
    # Compact homepage list, newest-first: year as the mono key + system title.
    return "\n".join(
        f'<li><span class="k">{esc(s["year"])}</span> {esc(s["title"])}</li>'
        for s in _engineering_by_year(d)
    )


# ---------------------------------------------------------------- JSON-LD (SEO)
PERSON_ID = "https://zafaryab.github.io/#person"


def _jsonld_script(obj) -> str:
    """Serialize to a safe <script type=application/ld+json> block.
    JSON is not HTML-escaped, so neutralise the three characters that could
    break out of the script element."""
    payload = json.dumps(obj, indent=2, ensure_ascii=False)
    payload = (payload.replace("<", "\\u003c")
                      .replace(">", "\\u003e")
                      .replace("&", "\\u0026"))
    return f'<script type="application/ld+json">\n{payload}\n</script>'


def _person_node(d) -> dict:
    p = d["person"]
    return {
        "@type": "Person",
        "@id": PERSON_ID,
        "name": p["name"],
        "url": p["url"],
        "image": p["image"],
        "jobTitle": p["jobTitle"],
        "affiliation": {"@type": "Organization", "name": p["affiliation"]},
        "sameAs": list(p["sameAs"]),
        "knowsAbout": list(p["knowsAbout"]),
    }


def render_index_jsonld(d) -> str:
    node = {"@context": "https://schema.org"}
    node.update(_person_node(d))
    return _jsonld_script(node)


def render_resume_jsonld(d) -> str:
    # Person + one ScholarlyArticle node per published/accepted paper.
    # Under-review work is omitted (no public venue/link to cite).
    graph = [_person_node(d)]
    for p in d["publications"]["published"] + d["publications"]["accepted"]:
        art = {
            "@type": "ScholarlyArticle",
            "name": p["title"],
            "author": p["authors"],
            "isPartOf": {"@type": "Periodical", "name": p["venue"]},
        }
        if p.get("year"):
            art["datePublished"] = str(p["year"])
        links = p.get("links") or []
        if links:
            art["url"] = links[0]["href"]
        graph.append(art)
    return _jsonld_script({"@context": "https://schema.org", "@graph": graph})


SECTIONS = {
    INDEX: {"index-focus": render_focus, "index-counters": render_counters,
            "index-selected": render_selected, "index-selected-count": render_selected_count,
            "index-engineering": render_engineering_home,
            "index-jsonld": render_index_jsonld},
    RESUME: {"resume-current": render_current,
             "resume-publications": render_publications,
             "resume-patents": render_patents,
             "resume-engineering": render_engineering,
             "resume-jsonld": render_resume_jsonld},
}


# ---------------------------------------------------------------- injection
def inject(text: str, name: str, content0: str) -> str:
    s, e = f"<!-- build:{name}:start -->", f"<!-- build:{name}:end -->"
    if s not in text or e not in text:
        sys.exit(f"ERROR: markers for '{name}' not found in file.")
    si, ei = text.index(s), text.index(e)
    indent = text[text.rfind("\n", 0, si) + 1:si]
    body = "\n".join((indent + ln if ln.strip() else ln) for ln in content0.splitlines())
    return text[:si] + s + "\n" + body + "\n" + indent + e + text[ei + len(e):]


def apply_file(path: Path, data: dict) -> str:
    text = path.read_text(encoding="utf-8")
    for name, fn in SECTIONS[path].items():
        text = inject(text, name, fn(data))
    return text


# ---------------------------------------------------------------- validation
def validate(d: dict) -> list[str]:
    errs: list[str] = []
    pubs = d["publications"]
    all_pubs = pubs["published"] + pubs["accepted"] + pubs["under_review"]

    titles = set()
    for p in all_pubs:
        for field in ("venue", "title", "authors", "me", "tags", "status"):
            if not p.get(field):
                errs.append(f"publication missing '{field}': {p.get('title', '?')}")
        # year required for published/accepted; may be null (dash) while under review
        if p.get("status") != "under_review" and not p.get("year"):
            errs.append(f"published/accepted publication missing year: {p.get('title')}")
        if p.get("status") not in STATUS_LABEL:
            errs.append(f"bad status '{p.get('status')}': {p.get('title')}")
        if p.get("me") and p["me"] not in p.get("authors", ""):
            errs.append(f"author '{p['me']}' not in author list: {p['title']}")
        t = p.get("title")
        if t in titles:
            errs.append(f"duplicate publication title: {t}")
        titles.add(t)
        for l in p.get("links", []):
            if not str(l.get("href", "")).startswith("http"):
                errs.append(f"bad link on {t}: {l}")

    pnums = [p["n"] for p in d["patents"]]
    if len(pnums) != len(set(pnums)):
        errs.append("duplicate patent numbers")
    for p in d["patents"]:
        for l in p.get("links", []):
            if not str(l.get("href", "")).startswith("http"):
                errs.append(f"bad patent link on {p['n']}: {l}")

    # counters are computed from the data (source) — just validate they resolve
    valid_sources = set(counts(d))
    for c in d["counters"]:
        if "source" in c:
            if c["source"] not in valid_sources:
                errs.append(f"counter references unknown source: {c['source']}")
        elif "value" not in c:
            errs.append(f"counter missing value/source: {c.get('label')}")

    fnums = [f["n"] for f in d["focus"]]
    if len(fnums) != len(set(fnums)):
        errs.append("duplicate focus numbers")

    sel = _selected_items(d)
    orders = [r["homepage"].get("order") for _, r in sel]
    if len(orders) != len(set(orders)):
        errs.append("duplicate homepage.order in selected research")
    if orders and sorted(orders) != list(range(1, len(orders) + 1)):
        errs.append(f"homepage.order must be contiguous from 1: got {sorted(orders)}")
    for kind, r in sel:
        hp = r["homepage"]
        who = r.get("id") or r.get("title", "?")
        if not hp.get("summary"):
            errs.append(f"homepage missing 'summary': {who}")
        if kind == "pub" and not hp.get("code"):
            errs.append(f"homepage publication missing 'code': {who}")

    person = d.get("person", {})
    for field in ("name", "url", "image", "jobTitle", "affiliation", "sameAs", "knowsAbout"):
        if not person.get(field):
            errs.append(f"person missing '{field}' (needed for JSON-LD)")
    for u in person.get("sameAs", []):
        if not str(u).startswith("http"):
            errs.append(f"person sameAs not a URL: {u}")

    eng_titles = set()
    for s in d.get("engineering", []):
        for field in ("title", "year", "cat", "desc"):
            if not s.get(field):
                errs.append(f"engineering system missing '{field}': {s.get('title', '?')}")
        if s.get("title") in eng_titles:
            errs.append(f"duplicate engineering system: {s['title']}")
        eng_titles.add(s.get("title"))
    return errs


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description="Generate research HTML from data/research.json")
    ap.add_argument("--check", action="store_true",
                    help="validate data and report stale HTML without writing")
    args = ap.parse_args()

    try:
        data = json.loads(DATA.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"ERROR: {DATA} is not valid JSON: {exc}")

    errs = validate(data)
    stale = []
    for path in (INDEX, RESUME):
        if apply_file(path, data) != path.read_text(encoding="utf-8"):
            stale.append(path.name)

    if args.check:
        print("Research data check")
        print(f"  Publications: {sum(len(v) for v in data['publications'].values())}"
              f"  Patents: {len(data['patents'])}")
        print(f"  Validation errors: {len(errs)}")
        for e in errs:
            print(f"    ERROR: {e}")
        print(f"  Stale generated HTML: {', '.join(stale) if stale else 'none'}"
              + ("  (run: python scripts/build_research.py)" if stale else ""))
        sys.exit(1 if errs or stale else 0)

    if errs:
        print("Refusing to build — data validation failed:")
        for e in errs:
            print(f"  ERROR: {e}")
        sys.exit(1)

    for path in (INDEX, RESUME):
        path.write_text(apply_file(path, data), encoding="utf-8")
    print(f"Generated research HTML into index.html, resume.html"
          + (f"  ({', '.join(stale)} updated)" if stale else "  (already up to date)"))


if __name__ == "__main__":
    main()
