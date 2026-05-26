#!/usr/bin/env python3
"""Извлечение текста, постраничных PNG и иллюстраций из PDF.

Обёртка над poppler-utils (pdftotext / pdftoppm / pdfimages). Делает ровно три
вещи, чтобы Claude-агенту не приходилось каждый раз угадывать флаги.

Использование:
    python core/scripts/extract.py books/<имя>.pdf result/<имя>/extracted/

После успешного запуска в out/ появится:
    text.txt              — pdftotext -layout
    pages/page-NNNN.png   — pdftoppm -png -r 200
    images/img-NNN.<ext>  — pdfimages -all
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


REQUIRED_TOOLS = ["pdftotext", "pdftoppm", "pdfimages"]


def check_tools() -> None:
    missing = [t for t in REQUIRED_TOOLS if shutil.which(t) is None]
    if missing:
        sys.stderr.write(
            "Отсутствуют утилиты poppler-utils: " + ", ".join(missing) + "\n"
            "Установка:\n"
            "  - Debian/Ubuntu:   sudo apt install poppler-utils\n"
            "  - macOS (brew):    brew install poppler\n"
            "  - Windows (choco): choco install poppler\n"
        )
        sys.exit(2)


def run(cmd: list[str]) -> None:
    print("$ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("pdf", type=Path, help="Путь к исходному PDF.")
    parser.add_argument("out", type=Path, help="Папка для вывода (будет создана).")
    parser.add_argument("--resolution", type=int, default=200, help="DPI постраничных PNG (по умолчанию 200).")
    parser.add_argument("--force", action="store_true", help="Перезаписать существующие подпапки.")
    args = parser.parse_args()

    if not args.pdf.is_file():
        sys.stderr.write(f"PDF не найден: {args.pdf}\n")
        return 1

    check_tools()

    out: Path = args.out
    out.mkdir(parents=True, exist_ok=True)

    text_path = out / "text.txt"
    pages_dir = out / "pages"
    images_dir = out / "images"

    if not args.force and (text_path.exists() or any(pages_dir.glob("*")) or any(images_dir.glob("*"))):
        sys.stderr.write(
            f"В {out} уже есть результаты предыдущей экстракции. "
            "Запусти с --force, чтобы перезаписать.\n"
        )
        return 1

    pages_dir.mkdir(exist_ok=True)
    images_dir.mkdir(exist_ok=True)

    run(["pdftotext", "-layout", str(args.pdf), str(text_path)])
    run(["pdftoppm", "-png", "-r", str(args.resolution), str(args.pdf), str(pages_dir / "page")])
    run(["pdfimages", "-all", str(args.pdf), str(images_dir / "img")])

    pages_count = len(list(pages_dir.glob("page-*.png")))
    images_count = sum(1 for _ in images_dir.iterdir())
    text_size_kb = text_path.stat().st_size // 1024

    print()
    print(f"OK. text.txt={text_size_kb} KB, pages={pages_count}, images={images_count}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
