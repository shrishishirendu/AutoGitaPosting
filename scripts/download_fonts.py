from __future__ import annotations

import urllib.request
from pathlib import Path


def main() -> None:
    url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf"
    target_dir = Path(__file__).resolve().parents[1] / "fonts"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / "NotoSansDevanagari-Regular.ttf"
    print(f"Downloading font to {target_path}")
    urllib.request.urlretrieve(url, target_path)
    print("Done.")


if __name__ == "__main__":
    main()
