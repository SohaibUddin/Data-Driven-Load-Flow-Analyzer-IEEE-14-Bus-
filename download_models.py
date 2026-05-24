"""
download_models.py
==================
Downloads the 7 trained gradient-boosting models from the GitHub Release
assets and places them in the local ./models/ directory.

The model files are 60–70 MB each (~470 MB total) and are too large to
commit directly to the Git repository, so they are released as binary
assets attached to a GitHub Release tag.

USAGE
-----
    python download_models.py

You only need to run this script once after cloning the repository.

REQUIREMENTS
------------
    requests   (`pip install requests`)
    tqdm       (`pip install tqdm`)        — optional, for progress bars
"""
import os
import sys
import urllib.request

# =============================================================================
#  CONFIGURATION
#  ── Update these two constants after you publish your first GitHub Release
# =============================================================================
GITHUB_USERNAME = "<SohaibUddin>"          
REPO_NAME       = "data-driven-load-flow-analyser"
RELEASE_TAG     = "v1.0.0"                   

MODEL_FILES = [
    "Voltage_Model.joblib",
    "Angle_Model.joblib",
    "SendingP_Model.joblib",
    "ReceivingP_Model.joblib",
    "SendingQ_Model.joblib",
    "ReceivingQ_Model.joblib",
    "Iline_Model.joblib",
]

# =============================================================================
#  IMPLEMENTATION
# =============================================================================
BASE_URL = (
    f"https://github.com/{GITHUB_USERNAME}/{REPO_NAME}"
    f"/releases/download/{RELEASE_TAG}"
)

DEST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
os.makedirs(DEST_DIR, exist_ok=True)


def _format_bytes(num: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024.0:
            return f"{num:6.2f} {unit}"
        num /= 1024.0
    return f"{num:.2f} TB"


def _download(url: str, dest_path: str) -> None:
    """Download a single file with a console progress indicator."""
    print(f"  → {os.path.basename(dest_path)}")
    try:
        with urllib.request.urlopen(url) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            done = 0
            chunk_size = 64 * 1024  # 64 KB
            with open(dest_path, "wb") as fh:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    fh.write(chunk)
                    done += len(chunk)
                    if total:
                        pct = done * 100 / total
                        sys.stdout.write(
                            f"\r      {_format_bytes(done)} / {_format_bytes(total)}  "
                            f"({pct:5.1f}%)"
                        )
                        sys.stdout.flush()
            sys.stdout.write("\n")
    except Exception as e:
        sys.stdout.write("\n")
        print(f"      FAILED: {e}")
        if os.path.isfile(dest_path):
            os.remove(dest_path)
        raise


def main() -> int:
    if GITHUB_USERNAME == "<your-username>":
        print("ERROR: Please edit download_models.py and set GITHUB_USERNAME "
              "to your actual GitHub username before running.")
        return 1

    print(f"Downloading {len(MODEL_FILES)} model files from:")
    print(f"  {BASE_URL}\n")

    failed = []
    skipped = []
    for fname in MODEL_FILES:
        dest = os.path.join(DEST_DIR, fname)
        if os.path.isfile(dest) and os.path.getsize(dest) > 1024:
            print(f"  ✓ {fname}  (already present, skipping)")
            skipped.append(fname)
            continue
        try:
            _download(f"{BASE_URL}/{fname}", dest)
        except Exception:
            failed.append(fname)

    print()
    print("=" * 60)
    print(f"Downloaded : {len(MODEL_FILES) - len(failed) - len(skipped)}")
    print(f"Skipped    : {len(skipped)}  (already on disk)")
    print(f"Failed     : {len(failed)}")
    if failed:
        print(f"\nFailed files: {failed}")
        print("Check the release tag and your internet connection, then retry.")
        return 1
    print("\nAll model files are in:")
    print(f"  {DEST_DIR}")
    print("\nYou can now run the dashboard:  python main.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
