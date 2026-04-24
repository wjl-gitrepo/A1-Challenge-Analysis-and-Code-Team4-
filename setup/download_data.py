"""Download large data files needed to run the UHI prediction notebooks.

Large files (TIFFs + Building_Footprint_Data.zip) exceed GitHub's 100 MB
file limit and are hosted externally. This script downloads them into
the correct locations in the repo.

USAGE:
    python setup/download_data.py

If downloads fail (network timeout, rate limit), you can manually download
each file from the shared folder and place it at the path listed below.
"""
from __future__ import annotations

import os
import sys
import urllib.request
import zipfile
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════
# CONFIG — REPLACE the DRIVE_BASE_URL with your actual shared folder.
# Google Drive direct-download format:
#   https://drive.google.com/uc?export=download&id=FILE_ID
# Or use OneDrive / Dropbox direct links.
# ═══════════════════════════════════════════════════════════════════
DRIVE_BASE_URL = "https://drive.google.com/uc?export=download&id="

# Replace each FILE_ID with the actual Google Drive file ID
FILES = [
    {
        "name": "S2_median_Chile.tiff",
        "dest": "S2_median_Chile.tiff",
        "size_mb": 664,
        "file_id": "REPLACE_WITH_CHILE_TIFF_FILE_ID",
    },
    {
        "name": "S2_median_Brazil.tiff",
        "dest": "S2_median_Brazil.tiff",
        "size_mb": 640,
        "file_id": "REPLACE_WITH_BRAZIL_TIFF_FILE_ID",
    },
    {
        "name": "S2_median_Sierra.tiff",
        "dest": "S2_median_Sierra.tiff",
        "size_mb": 280,
        "file_id": "REPLACE_WITH_SIERRA_TIFF_FILE_ID",
    },
    {
        "name": "Building_Footprint_Data.zip",
        "dest": "Data/Building_Footprint_Data.zip",
        "size_mb": 184,
        "file_id": "REPLACE_WITH_BUILDINGS_ZIP_FILE_ID",
        "unzip_to": "Data/",
    },
]


def _progress(blocks_done, block_size, total_size):
    pct = min(100, 100 * blocks_done * block_size / max(1, total_size))
    bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
    sys.stdout.write(f"\r    [{bar}] {pct:5.1f}%")
    sys.stdout.flush()


def download_one(name: str, dest: str, file_id: str, size_mb: int,
                 unzip_to: str | None = None) -> bool:
    dest_path = Path(dest)
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if dest_path.exists() and dest_path.stat().st_size > 1_000_000:
        print(f"  ✓ {name} already exists — skipping")
        if unzip_to:
            _try_unzip(dest_path, unzip_to)
        return True

    if file_id.startswith("REPLACE_WITH"):
        print(f"  ✗ {name}: file_id not configured in setup/download_data.py")
        print(f"    Manually download this file to: {dest}")
        return False

    url = DRIVE_BASE_URL + file_id
    print(f"\n  ↓ downloading {name} (~{size_mb} MB)")
    try:
        urllib.request.urlretrieve(url, dest_path, reporthook=_progress)
        print()
        if unzip_to:
            _try_unzip(dest_path, unzip_to)
        return True
    except Exception as e:
        print(f"\n  ✗ download failed: {e}")
        print(f"    Manually download to: {dest}")
        return False


def _try_unzip(zip_path: Path, extract_to: str):
    extract_path = Path(extract_to)
    extract_path.mkdir(parents=True, exist_ok=True)
    print(f"  ↻ extracting {zip_path.name} to {extract_to}")
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_path)
        print(f"  ✓ extracted")
    except Exception as e:
        print(f"  ✗ extract failed: {e}")


def main():
    print("═" * 65)
    print("  Business Challenge II — Data Downloader")
    print("═" * 65)
    print(
        "\n  Downloading large data files (TIFFs + building footprints)."
        "\n  Total: ~1.8 GB. Allow 10–30 min depending on connection."
    )
    print()

    ok_count = 0
    for f in FILES:
        if download_one(f["name"], f["dest"], f["file_id"],
                        f["size_mb"], f.get("unzip_to")):
            ok_count += 1

    print()
    print("═" * 65)
    if ok_count == len(FILES):
        print(f"  ✅ All {ok_count}/{len(FILES)} files ready")
        print(
            "\n  Next step: open notebooks/ and run them in order 01 → 02 → 03 → 04 → 05"
        )
    else:
        print(f"  ⚠ {ok_count}/{len(FILES)} downloaded. Check errors above.")
        print(
            "\n  For files that failed, manually download from the shared "
            "\n  folder and place them at the paths listed."
        )
    print("═" * 65)


if __name__ == "__main__":
    main()
