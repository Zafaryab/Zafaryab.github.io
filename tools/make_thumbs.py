#!/usr/bin/env python3
from pathlib import Path
from PIL import Image, ImageOps

# Folders
FULL_DIR = Path("images/gallery/full")
THUMB_DIR = Path("images/gallery/thumbs")

# Thumbnail settings
MAX_WIDTH = 900          # change to 600–1200 as you like
QUALITY = 82             # JPEG/WebP quality (0–100)
FORMATS = {".jpg", ".jpeg", ".png", ".webp"}

def make_thumb(src: Path, dst: Path):
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im)  # fixes rotated images from camera EXIF
        w, h = im.size

        # If already smaller than target width, still copy as "thumb" (optional)
        if w > MAX_WIDTH:
            new_h = int(h * (MAX_WIDTH / w))
            im = im.resize((MAX_WIDTH, new_h), Image.Resampling.LANCZOS)

        dst.parent.mkdir(parents=True, exist_ok=True)

        ext = dst.suffix.lower()
        if ext in {".jpg", ".jpeg"}:
            im = im.convert("RGB")  # ensure no alpha channel
            im.save(dst, quality=QUALITY, optimize=True, progressive=True)
        elif ext == ".png":
            im.save(dst, optimize=True)
        elif ext == ".webp":
            im.save(dst, quality=QUALITY, method=6)
        else:
            # fallback
            im.save(dst)

def main():
    if not FULL_DIR.exists():
        raise SystemExit(f"❌ Full directory not found: {FULL_DIR}")

    THUMB_DIR.mkdir(parents=True, exist_ok=True)

    made = 0
    skipped = 0

    for src in FULL_DIR.rglob("*"):
        if not src.is_file() or src.suffix.lower() not in FORMATS:
            continue

        dst = THUMB_DIR / src.name  # same filename in thumbs/
        if dst.exists() and dst.stat().st_mtime >= src.stat().st_mtime:
            skipped += 1
            continue

        make_thumb(src, dst)
        made += 1
        print(f"✅ {src.name} -> thumbs/{dst.name}")

    print(f"\nDone. Created: {made}, Skipped (up-to-date): {skipped}")

if __name__ == "__main__":
    main()
