---
description: Собрать главу: создать index.md, перерисовать nav, прогнать mkdocs build --strict.
argument-hint: <имя_книги> <номер_главы>
---

# /assemble-chapter

Финализировать главу `$2` книги `$1`: убедиться, что все её разделы прошли ревью, создать/обновить `chapters/<NN-slug>/index.md`, перегенерировать `mkdocs.yml`, прогнать `mkdocs build --strict`, переключить разделы в `[x]`.

## Предусловие

Все разделы главы `$2` в `result/$1/translation/PROGRESS.md` должны быть в `[r]` или `[x]`. Если нет — выведи список незаконченных и остановись.

## Алгоритм

1. Прочитай `perevodnik/CLAUDE.md` и `result/$1/translation/TRANSLATION_GUIDE.md` (§10).
2. Загляни в `result/$1/translation/PROGRESS.md` — убедись в предусловии.
3. Запусти **один** `Agent` с промптом «Сборщик главы» из `result/$1/translation/AGENT_PROMPTS.md` (роль D), подставив номер главы.
4. Если сборщик завершился без ошибок — он сам перегнал `[r] → [x]` для всех разделов главы и прогнал `mkdocs build --strict`. Сообщи пользователю.
5. Если упал `mkdocs build` — статусы НЕ переключай, покажи ошибку пользователю.
