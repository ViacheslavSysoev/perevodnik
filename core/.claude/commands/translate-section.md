---
description: Перевести один раздел книги. Тонкая обёртка над ролью «Переводчик» из AGENT_PROMPTS.md.
argument-hint: <имя_книги> <N.M>
---

# /translate-section

Перевести единственный раздел `$2` книги `$1`. Полезно для дозапуска отдельных разделов вручную, когда orchestrator уже завершил работу или ты хочешь обкатать новую секцию изолированно.

## Алгоритм

1. Прочитай `perevodnik/CLAUDE.md` и `result/$1/translation/TRANSLATION_GUIDE.md`.
2. Прочитай `result/$1/translation/chapter_map.json`. Найди раздел `$2` — там есть `lines`, `pages`, `title_en`, `title_ru`, slug главы.
3. Если в `result/$1/translation/PROGRESS.md` раздел уже в `[~]`/`[r]`/`[x]` — спроси пользователя, действительно ли перезаписать.
4. Запусти **один** `Agent` с промптом «Переводчик раздела» из `result/$1/translation/AGENT_PROMPTS.md` (роль B), подставив значения из chapter_map.
5. После завершения покажи пользователю diff `result/$1/docs/chapters/<NN-slug>/section-$2.md` и обновлённую строку в `PROGRESS.md`.
