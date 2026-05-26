#!/usr/bin/env python3
"""Инициализация рабочей папки книги из шаблона.

Принимает путь к book.yml (который orchestrator-агент уже создал в result/<имя>/),
копирует шаблоны из core/templates/<target_language>/ в result/<имя>/translation/,
создаёт скелет docs/ и рендерит mkdocs.yml. chapter_map.json и финальный nav
заполняются картографом + render_mkdocs.py отдельно.

Использование:
    python core/scripts/init_book.py result/<имя>/book.yml
"""

import argparse
import shutil
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

COPY_VERBATIM = [
    "TRANSLATION_GUIDE.md",
    "GLOSSARY.md",
    "PROGRESS.md",
    "AGENT_PROMPTS.md",
    "DOMAIN.md",
]


def _fill_defaults(book: dict) -> dict:
    """Заполнить отсутствующие необязательные поля, чтобы шаблон не падал на StrictUndefined."""
    book.setdefault("features", {})
    book["features"].setdefault("math", True)
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
    return book


def render_mkdocs(book: dict, book_dir: Path, lang: str) -> None:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_ROOT / lang)),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )
    template = env.get_template("mkdocs.yml.j2")
    # На этапе init глав ещё нет — рендерим с пустым списком, render_mkdocs.py
    # перерендерит уже с реальным chapter_map.json.
    rendered = template.render(book=_fill_defaults(book), chapters=[])
    (book_dir / "mkdocs.yml").write_text(rendered, encoding="utf-8")


def make_docs_skeleton(book: dict, book_dir: Path) -> None:
    docs = book_dir / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "assets" / "figures").mkdir(parents=True, exist_ok=True)
    (docs / "assets" / "javascripts").mkdir(parents=True, exist_ok=True)
    (docs / "assets" / "stylesheets").mkdir(parents=True, exist_ok=True)
    (docs / "chapters").mkdir(exist_ok=True)

    title_translated = book["title_translated"]
    title_original = book["title_original"]
    attribution = book["license"]["attribution"]
    license_type = book["license"]["type"]
    license_url = book["license"].get(
        "url", "https://creativecommons.org/licenses/by-nc-sa/4.0/"
    )
    source_url = book["license"].get("attribution_url", "")

    index = docs / "index.md"
    if not index.exists():
        index.write_text(
            f"# {title_translated}\n\n"
            f"Русский перевод книги «{title_original}» ({attribution}).\n\n"
            f"Лицензия: [{license_type}]({license_url}). "
            + (f"Оригинал: [{source_url}]({source_url}).\n" if source_url else "\n"),
            encoding="utf-8",
        )

    about = docs / "about.md"
    if not about.exists():
        about.write_text(
            f"# О книге\n\n"
            f"Это русский перевод книги «{title_original}» ({attribution}),\n"
            f"распространяемой по лицензии [{license_type}]({license_url}).\n\n"
            + (
                f"Оригинал доступен по адресу: <{source_url}>.\n\n"
                if source_url
                else ""
            )
            + "Перевод подготовлен с помощью открытого пайплайна "
            "[perevodnik](https://github.com/) и распространяется на условиях "
            "той же лицензии.\n",
            encoding="utf-8",
        )

    # Минимальная конфигурация MathJax (если features.math включён в book.yml).
    if book.get("features", {}).get("math", True):
        mathjax_js = docs / "assets" / "javascripts" / "mathjax-config.js"
        if not mathjax_js.exists():
            mathjax_js.write_text(
                "window.MathJax = {\n"
                "  tex: { inlineMath: [['\\\\(', '\\\\)']], displayMath: [['\\\\[', '\\\\]']] },\n"
                "  options: { ignoreHtmlClass: '.*|', processHtmlClass: 'arithmatex' }\n"
                "};\n",
                encoding="utf-8",
            )

    extra_css = docs / "assets" / "stylesheets" / "extra.css"
    if not extra_css.exists():
        extra_css.write_text("/* добавь сюда переопределения стилей */\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("book_yml", type=Path, help="Путь к book.yml в result/<имя>/.")
    args = parser.parse_args()

    if not args.book_yml.is_file():
        sys.stderr.write(f"book.yml не найден: {args.book_yml}\n")
        return 1

    book = yaml.safe_load(args.book_yml.read_text(encoding="utf-8"))
    if not book:
        sys.stderr.write(f"book.yml пустой: {args.book_yml}\n")
        return 1

    lang = book.get("target_language", "ru")
    template_dir = TEMPLATES_ROOT / lang
    if not template_dir.is_dir():
        sys.stderr.write(
            f"Нет шаблонов для языка {lang!r}. "
            f"Доступны: {[p.name for p in TEMPLATES_ROOT.iterdir() if p.is_dir()]}\n"
        )
        return 1

    book_dir = args.book_yml.parent
    translation_dir = book_dir / "translation"
    translation_dir.mkdir(exist_ok=True)

    for name in COPY_VERBATIM:
        src = template_dir / name
        dst = translation_dir / name
        if src.is_file() and not dst.exists():
            shutil.copy(src, dst)

    # Пустые JSON-карты — заполнит картограф / переводчики.
    chapter_map = translation_dir / "chapter_map.json"
    if not chapter_map.exists():
        chapter_map.write_text("{}\n", encoding="utf-8")

    figure_map = translation_dir / "figure_map.json"
    if not figure_map.exists():
        figure_map.write_text("{}\n", encoding="utf-8")

    make_docs_skeleton(book, book_dir)
    render_mkdocs(book, book_dir, lang)

    print(f"OK. Книга инициализирована: {book_dir}")
    print("Следующий шаг: python core/scripts/extract.py <PDF> "
          f"{book_dir / 'extracted'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
