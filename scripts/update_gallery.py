#!/usr/bin/env python3
"""
update_gallery.py — non-destructive gallery maintainer for ZH://RESEARCH.

Workflow:
    1. drop new photographs into  images/gallery/full/
    2. run                       python scripts/update_gallery.py
    3. edit only the descriptive fields for new entries in data/photos.json

What it does
    * scans images/gallery/full/ for photographs
    * for each NEW photo (not already in the manifest):
        - assigns a stable id            (frame-0001, frame-0002, ...)
        - normalizes the filename        (frame-0001.jpg)
        - generates a WebP thumbnail     (images/gallery/thumbs/frame-0001.webp)
        - records safe technical metadata (width, height, orientation, capture date)
        - appends a JSON entry with empty, ready-to-edit curator fields
    * regenerates any missing thumbnails for existing entries
    * validates the manifest and prints a concise summary

Guarantees
    * curator-maintained fields are NEVER overwritten
    * original JPGs are never modified
    * GPS / device-serial EXIF is never written to the public JSON
    * running twice without new photos changes nothing (idempotent)

Usage
    python scripts/update_gallery.py            # sync (add new photos)
    python scripts/update_gallery.py --check     # validate only, no changes
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    from PIL import Image, ImageOps, ExifTags
except ImportError:  # pragma: no cover
    sys.exit("Pillow is required:  pip install Pillow")

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
FULL_DIR = ROOT / "images" / "gallery" / "full"
THUMB_DIR = ROOT / "images" / "gallery" / "thumbs"
JSON_PATH = ROOT / "data" / "photos.json"

# JSON stores web-root-relative POSIX paths
FULL_REL = "images/gallery/full"
THUMB_REL = "images/gallery/thumbs"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
THUMB_LONG_EDGE = 800          # px, long edge of generated thumbnails
THUMB_QUALITY = 82             # WebP quality
ID_PREFIX = "frame-"

# Fields the script owns and may (re)write on the entries it creates.
# Everything else is curator-maintained and is never touched once written.
CURATOR_FIELDS = (
    "title", "subtitle", "category", "tags",
    "collections", "location", "date", "featured", "order",
)

_DATETIME_TAG = next((k for k, v in ExifTags.TAGS.items() if v == "DateTimeOriginal"), 36867)


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def basename(path: str) -> str:
    return Path(path).name


def load_manifest() -> list:
    if not JSON_PATH.exists():
        return []
    try:
        data = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        sys.exit(f"ERROR: {JSON_PATH} is not valid JSON: {exc}")
    if not isinstance(data, list):
        sys.exit(f"ERROR: {JSON_PATH} must contain a JSON array.")
    return data


def serialize(data: list) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def next_id_number(data: list) -> int:
    nums = [0]
    for e in data:
        m = re.fullmatch(rf"{ID_PREFIX}(\d+)", str(e.get("id", "")))
        if m:
            nums.append(int(m.group(1)))
    return max(nums) + 1


def orientation_of(w: int, h: int) -> str:
    if w > h:
        return "landscape"
    if h > w:
        return "portrait"
    return "square"


def safe_capture_date(im: Image.Image) -> str:
    """Return capture date as YYYY-MM-DD, or '' — never touches GPS."""
    try:
        exif = im.getexif()
    except Exception:
        return ""
    raw = exif.get(_DATETIME_TAG)
    if not raw:
        return ""
    m = re.match(r"(\d{4})[:\-](\d{2})[:\-](\d{2})", str(raw))
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""


def make_thumb(src: Path, dst: Path) -> None:
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)          # respect EXIF orientation
        im.thumbnail((THUMB_LONG_EDGE, THUMB_LONG_EDGE), Image.Resampling.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.convert("RGB").save(dst, "WEBP", quality=THUMB_QUALITY, method=6)


def read_dimensions(src: Path) -> tuple[int, int, str, str]:
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)
        w, h = im.size
        date = safe_capture_date(im)
    return w, h, orientation_of(w, h), date


# ----------------------------------------------------------------------------
# Core
# ----------------------------------------------------------------------------
def scan_full() -> list[Path]:
    if not FULL_DIR.exists():
        sys.exit(f"ERROR: full directory not found: {FULL_DIR}")
    return sorted(
        p for p in FULL_DIR.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )


def validate(data: list, warnings: list) -> dict:
    """Collect integrity warnings without mutating the manifest."""
    stats = {"missing_files": 0, "missing_thumbs": 0}
    seen_ids, seen_fulls = set(), set()

    for e in data:
        eid = e.get("id", "<no-id>")
        full = e.get("full", "")
        thumb = e.get("thumb", "")

        if eid in seen_ids:
            warnings.append(f"duplicate id: {eid}")
        seen_ids.add(eid)

        if full in seen_fulls:
            warnings.append(f"duplicate file reference: {full}")
        seen_fulls.add(full)

        if full and not (ROOT / full).exists():
            warnings.append(f"entry {eid} references missing image: {full}")
            stats["missing_files"] += 1
        if thumb and not (ROOT / thumb).exists():
            warnings.append(f"entry {eid} references missing thumbnail: {thumb}")
            stats["missing_thumbs"] += 1

    # orphan thumbnails (present on disk but referenced by nobody)
    referenced_thumbs = {basename(e.get("thumb", "")) for e in data}
    if THUMB_DIR.exists():
        for t in THUMB_DIR.iterdir():
            if t.is_file() and t.name not in referenced_thumbs:
                warnings.append(f"orphan thumbnail (not referenced): {t.name}")
    return stats


def run(check_only: bool) -> int:
    data = load_manifest()
    warnings: list[str] = []
    existing_count = len(data)

    referenced = {basename(e.get("full", "")) for e in data}
    new_files = [p for p in scan_full() if p.name not in referenced]

    # ---- validation (both modes) ----
    stats = validate(data, warnings)

    if check_only:
        print("Gallery check (no changes made).\n")
        print(f"  Entries:          {existing_count}")
        print(f"  Unlisted photos:  {len(new_files)}"
              + (f"  -> {', '.join(p.name for p in new_files)}" if new_files else ""))
        print(f"  Missing files:    {stats['missing_files']}")
        print(f"  Missing thumbs:   {stats['missing_thumbs']}")
        print(f"  Warnings:         {len(warnings)}")
        for w in warnings:
            print(f"    WARNING: {w}")
        return 1 if (warnings or stats["missing_files"]) else 0

    # ---- regenerate missing thumbnails for existing entries (safe) ----
    thumbs_created = 0
    for e in data:
        full, thumb = e.get("full", ""), e.get("thumb", "")
        src, dst = ROOT / full, ROOT / thumb
        if full and thumb and src.exists() and not dst.exists():
            make_thumb(src, dst)
            thumbs_created += 1
            print(f"  rebuilt missing thumb: {thumb}")

    # ---- ingest new photographs ----
    next_num = next_id_number(data)
    added = 0
    for src in new_files:
        photo_id = f"{ID_PREFIX}{next_num:04d}"
        next_num += 1
        ext = src.suffix.lower()
        if ext == ".jpeg":
            ext = ".jpg"

        # normalize filename (stable technical name)
        target = FULL_DIR / f"{photo_id}{ext}"
        if target.exists():
            warnings.append(f"cannot normalize {src.name}: {target.name} already exists")
            continue
        src.rename(target)

        w, h, orient, date = read_dimensions(target)
        thumb_path = THUMB_DIR / f"{photo_id}.webp"
        make_thumb(target, thumb_path)
        thumbs_created += 1

        data.append({
            "id": photo_id,
            "title": "",
            "subtitle": "",
            "category": "uncategorized",
            "tags": [],
            "collections": [],
            "location": "",
            "date": date,
            "featured": False,
            "order": len(data) + 1,
            "thumb": f"{THUMB_REL}/{photo_id}.webp",
            "full": f"{FULL_REL}/{photo_id}{ext}",
            "width": w,
            "height": h,
            "orientation": orient,
        })
        added += 1
        print(f"  + {src.name}  ->  {photo_id}{ext}  (+ thumb, + entry)")

    # ---- write only if content actually changed ----
    new_text = serialize(data)
    changed = (not JSON_PATH.exists()) or JSON_PATH.read_text(encoding="utf-8") != new_text
    if changed:
        JSON_PATH.write_text(new_text, encoding="utf-8")

    # ---- summary ----
    if added == 0 and thumbs_created == 0 and not changed:
        print("No new photographs detected.\nGallery is up to date.")
    else:
        print("\nGallery update complete.\n")
    print(f"  Existing:       {existing_count}")
    print(f"  New:            {added}")
    print(f"  Thumbs created: {thumbs_created}")
    print(f"  Missing files:  {stats['missing_files']}")
    print(f"  Warnings:       {len(warnings)}")
    print(f"  Total:          {len(data)}")
    for w in warnings:
        print(f"    WARNING: {w}")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Sync the ZH://RESEARCH photo gallery.")
    ap.add_argument("--check", action="store_true",
                    help="validate the manifest without making any changes")
    args = ap.parse_args()
    sys.exit(run(check_only=args.check))


if __name__ == "__main__":
    main()
