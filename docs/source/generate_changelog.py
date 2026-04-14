from datetime import datetime
from pathlib import Path

CHANGELOG_DIR = Path(__file__).resolve().parents[1] / "changelog"


def datetime_extract(path: Path) -> datetime:
    date_string, _ = path.stem.split("-", maxsplit=1)
    return datetime.strptime(date_string, "%Y.%m.%d")


def main() -> None:
    changelog_entries = CHANGELOG_DIR.glob("*.rst")
    for path in reversed(sorted(changelog_entries, key=datetime_extract)):
        with path.open(mode="r") as f:
            lines = f.readlines()

        dt_obj = datetime_extract(path)
        print(f"\n* **{dt_obj:%Y.%m.%d}** - {lines[0]}")

        for line in lines[1:]:
            print(f"  {line}", end="")


if __name__ == "__main__":
    main()
