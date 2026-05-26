#!/usr/bin/env python3
"""Регенерация mkdocs.yml и PROGRESS.md из chapter_map.json.

Запускается после того, как картограф заполнил chapter_map.json, а также
каждый раз, когда сборщик главы хочет получить актуальный nav.

Использование:
    python core/scripts/render_mkdocs.py result/<имя>/
"""

import argparse
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

try:
    import yaml
except ImportError:
    sys.stderr.write("Нужна библиотека PyYAML: pip install -r requirements.txt\n")
    sys.exit(2)

try:
    from jinja2 import Environment, FileSystemLoader, StrictUndefined
except ImportError:
    sys.stderr.write("Нужна библиотека Jinja2: pip install -r requirements.txt\n")
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_ROOT = REPO_ROOT / "core" / "templates"


def render_progress(chapters: list[dict], existing: str | None) -> str:
    """Регенерирует тело PROGRESS.md, сохраняя существующие статусы и метаданные.

    Если раздел уже есть в существующем PROGRESS.md — берём его строку как есть.
    Если нет — добавляем новую строку со статусом `[ ]`.
    """
    existing_lines: dict[str, str] = {}
    if existing:
        for line in existing.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("- [") and "]" in stripped:
                # ключ: текст после "- [X] " до " — "
                rest = stripped.split("]", 1)[1].lstrip()
                key = rest.split(" — ", 1)[0].strip()
                existing_lines[key] = line

    out = [
        "# Прогресс перевода",
        "",
        "`[ ]` — не начато (pending), `[~]` — в работе (draft), "
        "`[r]` — на ревью (review), `[x]` — готово (done).",
        "",
        "Жизненный цикл раздела: переводчик `[ ] → [~]`, ревьюер `[~] → [r]`, "
        "сборщик `[r] → [x]` после успешного `mkdocs build --strict`.",
        "",
        "---",
        "",
    ]
    for ch in chapters:
        out.append(f"## Глава {ch['number']}. {ch['title_ru']}")
        out.append("")
        for sec in ch.get("sections", []):
            label = f"{sec['id']} {sec['title_ru']}"
            out.append(existing_lines.get(label, f"- [ ] {label}"))
        for end in ("Ключевые термины", "Резюме", "Упражнения"):
            if end in existing_lines:
                out.append(existing_lines[end])
            else:
                out.append(f"- [ ] {end}")
        out.append("")

    return "\n".join(out) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("book_dir", type=Path, help="Путь к result/<имя>/.")
    parser.add_argument("--only", choices=["mkdocs", "progress"], help="Перерисовать только указанный артефакт.")
    args = parser.parse_args()

    book_dir = args.book_dir
    if not (book_dir / "book.yml").is_file():
        sys.stderr.write(f"book.yml не найден: {book_dir / 'book.yml'}\n")
        return 1

    book = yaml.safe_load((book_dir / "book.yml").read_text(encoding="utf-8"))
    lang = book.get("target_language", "ru")
    # Те же дефолты, что в init_book.py, чтобы StrictUndefined-шаблон не упал.
    book.setdefault("features", {}); book["features"].setdefault("math", True)
    book.setdefault("parallelism", {})
    book["parallelism"].setdefault("translators", 4)
    book["parallelism"].setdefault("reviewers", 2)
    book.setdefault("site", {})
    book["site"].setdefault("repo_url", "")
    book["site"].setdefault("repo_name", book.get("name", ""))
    book["site"].setdefault("pages_url", "")
    book.setdefault("license", {})
    book["license"].setdefault("type", "Unknown")
    book["license"].setdefault("attribution", "")
    book["license"].setdefault("attribution_url", "")
    book["license"].setdefault("url", "")
    book.setdefault("site_description", f"Перевод книги «{book.get('title_original', '')}»")

    chapter_map_path = book_dir / "translation" / "chapter_map.json"
    if not chapter_map_path.is_file():
        sys.stderr.write(f"chapter_map.json не найден: {chapter_map_path}\n")
        return 1

    chapter_map = json.loads(chapter_map_path.read_text(encoding="utf-8")) or {}
    chapters = chapter_map.get("chapters", [])

    if args.only in (None, "mkdocs"):
        env = Environment(
            loader=FileSystemLoader(str(TEMPLATES_ROOT / lang)),
            undefined=StrictUndefined,
            keep_trailing_newline=True,
        )
        template = env.get_template("mkdocs.yml.j2")
        (book_dir / "mkdocs.yml").write_text(
            template.render(book=book, chapters=chapters), encoding="utf-8"
        )
        print(f"OK: {book_dir / 'mkdocs.yml'}")

    if args.only in (None, "progress"):
        progress_path = book_dir / "translation" / "PROGRESS.md"
        existing = progress_path.read_text(encoding="utf-8") if progress_path.exists() else None
        progress_path.write_text(render_progress(chapters, existing), encoding="utf-8")
        print(f"OK: {progress_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
