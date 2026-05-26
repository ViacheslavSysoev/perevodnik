#!/usr/bin/env python3
"""Парсер PROGRESS.md → JSON-сводка состояний.

orchestrator-агент вызывает этот скрипт в начале каждой сессии, чтобы решить,
какие агенты запускать дальше. Не читает chapter_map.json: PROGRESS.md — единый
источник истины о состоянии (содержит точно те же главы и разделы, потому что
сам генерируется из chapter_map.json при init).

Формат строки PROGRESS.md, который мы распознаём:
    - [ ] 1.3 Section title
    - [~] 1.3 Section title — Claude/Opus-4.7, 2026-05-18
    - [r] 1.3 Section title — …
    - [x] 1.3 Section title — …

Где `1.3` может быть и обычным маркером ("Ключевые термины", "Резюме", "Упражнения") —
такие end-of-chapter разделы тоже отслеживаются. Глава определяется заголовком
вида "## Глава N. …".

Использование:
    python core/scripts/progress.py result/<имя>/translation/PROGRESS.md
    → JSON в stdout
"""

import argparse
import json
import re
import sys
from pathlib import Path

# На Windows стандартный stdout — cp1252, что ломает кириллицу в названиях глав.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


STATUS_SYMBOLS = {" ": "pending", "~": "draft", "r": "review", "x": "done"}

CHAPTER_RE = re.compile(r"^##\s+Глава\s+(\d+)\.?\s*(.*?)\s*$")
ITEM_RE = re.compile(r"^\s*-\s*\[([ ~rx])\]\s+(.*?)\s*$")


def parse(path: Path) -> dict:
    chapters: list[dict] = []
    current: dict | None = None

    for raw in path.read_text(encoding="utf-8").splitlines():
        if m := CHAPTER_RE.match(raw):
            current = {
                "number": int(m.group(1)),
                "title": m.group(2),
                "items": [],
            }
            chapters.append(current)
            continue
        if m := ITEM_RE.match(raw):
            if current is None:
                continue
            symbol, body = m.group(1), m.group(2)
            label, _, meta = body.partition(" — ")
            current["items"].append(
                {
                    "label": label.strip(),
                    "status": STATUS_SYMBOLS[symbol],
                    "meta": meta.strip() or None,
                }
            )

    pending: list[dict] = []
    draft: list[dict] = []
    review: list[dict] = []
    done: list[dict] = []
    ready_to_assemble: list[int] = []
    fully_done_chapters: list[int] = []

    for ch in chapters:
        if not ch["items"]:
            continue
        statuses = {it["status"] for it in ch["items"]}
        for it in ch["items"]:
            entry = {"chapter": ch["number"], "label": it["label"]}
            if it["status"] == "pending":
                pending.append(entry)
            elif it["status"] == "draft":
                draft.append(entry)
            elif it["status"] == "review":
                review.append(entry)
            elif it["status"] == "done":
                done.append(entry)
        if statuses <= {"review", "done"} and "review" in statuses:
            ready_to_assemble.append(ch["number"])
        elif statuses == {"done"}:
            fully_done_chapters.append(ch["number"])

    total = sum(len(ch["items"]) for ch in chapters)
    done_count = len(done)

    return {
        "chapters_total": len(chapters),
        "items_total": total,
        "items_done": done_count,
        "completion": (done_count / total) if total else 0,
        "pending": pending,
        "draft": draft,
        "review": review,
        "done_count_by_chapter": {
            ch["number"]: sum(1 for it in ch["items"] if it["status"] == "done")
            for ch in chapters
        },
        "ready_to_assemble": ready_to_assemble,
        "fully_done_chapters": fully_done_chapters,
        "next_action": _next_action(pending, draft, review, ready_to_assemble, fully_done_chapters, len(chapters)),
    }


def _next_action(pending, draft, review, ready, fully_done, total_chapters: int) -> str:
    if pending:
        return "translate"
    if draft:
        return "review"
    if ready:
        return "assemble"
    if len(fully_done) == total_chapters and total_chapters > 0:
        return "build_site"
    return "idle"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("progress", type=Path, help="Путь к PROGRESS.md книги.")
    args = parser.parse_args()

    if not args.progress.is_file():
        sys.stderr.write(f"Файл не найден: {args.progress}\n")
        return 1

    json.dump(parse(args.progress), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
