---
description: Прогнать ревью одного раздела. Тонкая обёртка над ролью «Ревьюер» из AGENT_PROMPTS.md.
argument-hint: <имя_книги> <N.M>
---

# /review-section

Запустить ревью раздела `$2` книги `$1`.

## Алгоритм

1. Прочитай `perevodnik/CLAUDE.md` и `result/$1/translation/TRANSLATION_GUIDE.md` (особенно §9).
2. Найди раздел `$2` в `result/$1/translation/chapter_map.json` (нужны `lines`, `pages`, slug главы).
3. Проверь, что `result/$1/docs/chapters/<NN-slug>/section-$2.md` существует и его статус — `draft` или `review` (повторное ревью допускается).
4. Запусти **один** `Agent` с промптом «Ревьюер раздела» из `result/$1/translation/AGENT_PROMPTS.md` (роль C).
5. Если ревьюер вернул список FAIL — покажи его пользователю, статус оставь `draft`.
6. Если ревьюер сделал PASS и поменял `status: draft → review` и `[~] → [r]` в `PROGRESS.md` — сообщи пользователю.
