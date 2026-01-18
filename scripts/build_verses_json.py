from __future__ import annotations

from pathlib import Path

from gita_autoposter.dataset_builder import build_verses_json


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    vendor_dir = repo_root / "data" / "vendor" / "gita_gita"
    output_path = repo_root / "data" / "gita" / "verses.json"
    count = build_verses_json(vendor_dir, output_path)
    print(f"Wrote {count} verses to {output_path}")


if __name__ == "__main__":
    main()
