import json
from pathlib import Path


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    locales_dir = root / "src" / "boring" / "locales"
    en_path = locales_dir / "en.json"
    zh_path = locales_dir / "zh.json"

    en_data = load_json(en_path)
    zh_data = load_json(zh_path)

    en_keys = set(en_data.keys())
    zh_keys = set(zh_data.keys())

    missing_in_en = sorted(zh_keys - en_keys)
    missing_in_zh = sorted(en_keys - zh_keys)

    if missing_in_en:
        print("Missing keys in en.json:")
        for key in missing_in_en:
            print(f"  - {key}")
    if missing_in_zh:
        print("Missing keys in zh.json:")
        for key in missing_in_zh:
            print(f"  - {key}")

    return 1 if missing_in_en or missing_in_zh else 0


if __name__ == "__main__":
    raise SystemExit(main())
