import os
import json
import urllib.parse
import hashlib
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
#  Configuration
# ─────────────────────────────────────────────
REPO_OWNER = "roigoatzzz"
REPO_NAME  = "Glass-House"
BRANCH     = "main"
BASE_URL   = f"https://raw.githubusercontent.com/roigoatzzz/Glass-House/main/"

SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".webp", ".avif"}
SKIP_DIRS         = {".git", ".github", "node_modules", "__pycache__", ".vscode"}


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────
def file_hash(path: str) -> str:
    """MD5 of first 64 KB — fast duplicate detection."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        h.update(f.read(65536))
    return h.hexdigest()


def pretty_name(filename: str) -> str:
    """'my-cool_wallpaper.jpg' → 'My Cool Wallpaper'"""
    return Path(filename).stem.replace("-", " ").replace("_", " ").title()


def make_url(category: str, filename: str) -> str:
    path = f"{category}/{filename}".replace("\\", "/")
    return BASE_URL + urllib.parse.quote(path)


def format_size(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} GB"


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────
def generate(root: str = ".") -> None:
    data, seen_hashes = [], {}
    total_images = total_size = 0
    skipped_dups = []

    categories = sorted(
        d for d in os.listdir(root)
        if os.path.isdir(os.path.join(root, d))
        and not d.startswith(".")
        and d not in SKIP_DIRS
    )

    if not categories:
        print("⚠️  No category folders found. Run this from your repo root.")
        return

    for cat in categories:
        cat_path = os.path.join(root, cat)
        images   = []

        for filename in sorted(
            f for f in os.listdir(cat_path)
            if Path(f).suffix.lower() in SUPPORTED_FORMATS
        ):
            full_path = os.path.join(cat_path, filename)

            h = file_hash(full_path)
            if h in seen_hashes:
                skipped_dups.append(f"{cat}/{filename}  (dup of {seen_hashes[h]})")
                continue
            seen_hashes[h] = f"{cat}/{filename}"

            sz = os.path.getsize(full_path)
            total_size   += sz
            total_images += 1

            images.append({
                "name": pretty_name(filename),
                "url":  make_url(cat, filename),
                "file": filename,
                "size": sz,
            })

        if images:
            data.append({
                "category": cat.upper(),
                "slug":     cat.lower().replace(" ", "-"),
                "images":   images,
            })

    output = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "repo":         f"{REPO_OWNER}/{REPO_NAME}",
        "branch":       BRANCH,
        "total_images": total_images,
        "categories":   data,
    }

    out_path = os.path.join(root, "wallpapers.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # ── Summary ──────────────────────────────
    print()
    print("  ██████████████████████████████")
    print("  ██  VAULT  organizer.py      ██")
    print("  ██████████████████████████████")
    print()
    print(f"  ✅  wallpapers.json written")
    print(f"  📁  {len(data)} categories  |  🖼  {total_images} images  |  {format_size(total_size)}")
    print()
    for entry in data:
        bar  = "█" * min(len(entry["images"]), 28)
        name = entry["category"]
        print(f"  {name:<20}  {bar}  {len(entry['images'])}")
    if skipped_dups:
        print()
        print(f"  ⚠️  {len(skipped_dups)} duplicate(s) skipped:")
        for d in skipped_dups:
            print(f"      · {d}")
    print()


if __name__ == "__main__":
    import sys
    generate(sys.argv[1] if len(sys.argv) > 1 else ".")
