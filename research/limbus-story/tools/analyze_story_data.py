from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCALIZE = ROOT / "source-copy" / "Localize"
AUDIO_INDEX = ROOT / "audio-index" / "fmod_desktop_banks.csv"
OUT = ROOT / "analysis"

LANGS = ("kr", "en", "jp")
LANG_PREFIX = {"kr": "KR_", "en": "EN_", "jp": "JP_"}


def read_json(path: Path):
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def story_id_for(path: Path, lang: str) -> str:
    name = path.stem
    prefix = LANG_PREFIX[lang]
    if name.startswith(prefix):
        return name[len(prefix) :]
    return name


def story_group(story_id: str) -> str:
    match = re.match(r"^\d+([A-Z]+)", story_id)
    if match:
        return match.group(1)
    match = re.match(r"^([A-Z]+)", story_id)
    return match.group(1) if match else "unknown"


def load_audio_banks() -> dict[str, set[str]]:
    banks: dict[str, set[str]] = defaultdict(set)
    if not AUDIO_INDEX.exists():
        return banks
    with AUDIO_INDEX.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            banks[row["BankId"]].add(row["Kind"])
    return banks


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    file_rows: list[dict] = []
    field_counts: Counter[str] = Counter()
    lang_story_ids: dict[str, set[str]] = {lang: set() for lang in LANGS}
    field_by_lang: dict[str, Counter[str]] = {lang: Counter() for lang in LANGS}
    group_by_lang: dict[str, Counter[str]] = {lang: Counter() for lang in LANGS}
    total_rows_by_lang: Counter[str] = Counter()
    parse_errors: list[dict] = []

    for lang in LANGS:
        story_dir = LOCALIZE / lang / "StoryData"
        for path in sorted(story_dir.glob("*.json")):
            sid = story_id_for(path, lang)
            lang_story_ids[lang].add(sid)
            group = story_group(sid)
            group_by_lang[lang][group] += 1

            try:
                doc = read_json(path)
            except Exception as exc:  # pragma: no cover - diagnostic path
                parse_errors.append({"path": str(path), "error": repr(exc)})
                continue

            entries = doc.get("dataList", [])
            keys = Counter()
            for entry in entries:
                for key in entry.keys():
                    keys[key] += 1
                    field_counts[key] += 1
                    field_by_lang[lang][key] += 1
            total_rows_by_lang[lang] += len(entries)
            file_rows.append(
                {
                    "lang": lang,
                    "file": path.name,
                    "story_id": sid,
                    "group": group,
                    "entries": len(entries),
                    "fields": "|".join(sorted(keys)),
                    "bytes": path.stat().st_size,
                }
            )

    all_story_ids = set().union(*lang_story_ids.values())
    banks = load_audio_banks()

    audio_rows: list[dict] = []
    for sid in sorted(all_story_ids):
        kinds = banks.get(sid, set())
        audio_rows.append(
            {
                "story_id": sid,
                "group": story_group(sid),
                "in_kr": sid in lang_story_ids["kr"],
                "in_en": sid in lang_story_ids["en"],
                "in_jp": sid in lang_story_ids["jp"],
                "has_bank": "metadata-events" in kinds,
                "has_assets_bank": "sample-data" in kinds,
                "bank_kinds": "|".join(sorted(kinds)),
            }
        )

    coverage_rows: list[dict] = []
    for sid in sorted(all_story_ids):
        coverage_rows.append(
            {
                "story_id": sid,
                "group": story_group(sid),
                "kr": sid in lang_story_ids["kr"],
                "en": sid in lang_story_ids["en"],
                "jp": sid in lang_story_ids["jp"],
            }
        )

    field_rows = [
        {
            "field": field,
            "total_occurrences": count,
            "kr_occurrences": field_by_lang["kr"].get(field, 0),
            "en_occurrences": field_by_lang["en"].get(field, 0),
            "jp_occurrences": field_by_lang["jp"].get(field, 0),
        }
        for field, count in sorted(field_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    group_rows = []
    for group in sorted(set().union(*(set(c) for c in group_by_lang.values()))):
        group_rows.append(
            {
                "group": group,
                "kr_files": group_by_lang["kr"].get(group, 0),
                "en_files": group_by_lang["en"].get(group, 0),
                "jp_files": group_by_lang["jp"].get(group, 0),
            }
        )

    write_csv(
        OUT / "story-file-stats.csv",
        file_rows,
        ["lang", "file", "story_id", "group", "entries", "fields", "bytes"],
    )
    write_csv(
        OUT / "story-field-stats.csv",
        field_rows,
        ["field", "total_occurrences", "kr_occurrences", "en_occurrences", "jp_occurrences"],
    )
    write_csv(OUT / "story-group-stats.csv", group_rows, ["group", "kr_files", "en_files", "jp_files"])
    write_csv(OUT / "story-language-coverage.csv", coverage_rows, ["story_id", "group", "kr", "en", "jp"])
    write_csv(
        OUT / "story-audio-map.csv",
        audio_rows,
        ["story_id", "group", "in_kr", "in_en", "in_jp", "has_bank", "has_assets_bank", "bank_kinds"],
    )

    summary = {
        "languages": {
            lang: {
                "story_files": len(lang_story_ids[lang]),
                "dialogue_entries": total_rows_by_lang[lang],
                "groups": dict(sorted(group_by_lang[lang].items())),
            }
            for lang in LANGS
        },
        "unique_story_ids": len(all_story_ids),
        "story_ids_with_complete_language_coverage": sum(
            all(sid in lang_story_ids[lang] for lang in LANGS) for sid in all_story_ids
        ),
        "story_ids_with_bank_pair": sum(
            "metadata-events" in banks.get(sid, set()) and "sample-data" in banks.get(sid, set())
            for sid in all_story_ids
        ),
        "field_occurrences": dict(sorted(field_counts.items())),
        "parse_errors": parse_errors,
    }
    write_json(OUT / "story-analysis-summary.json", summary)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
