# Готовые промпты для запуска агентов

Шаблоны для вызова `Agent` (по умолчанию `subagent_type=general-purpose`). Перед запуском **подставь** конкретные значения вместо `<…>` — orchestrator делает это сам, читая `chapter_map.json` и `book.yml`. Все пути — относительно корня книги (`result/<имя>/`).

Все агенты должны прежде всего прочитать `CLAUDE.md` в корне `perevodnik/` и `translation/TRANSLATION_GUIDE.md` этой книги.

---

## A. Картограф (один запуск, разово, на этапе INIT)

**Цель:** заполнить `translation/chapter_map.json` — структуру глав/разделов, диапазоны строк в `extracted/text.txt` и страниц в `extracted/pages/`.

```
Прочитай perevodnik/CLAUDE.md и result/<имя>/translation/TRANSLATION_GUIDE.md.

Задание: сформировать result/<имя>/translation/chapter_map.json для книги «<title_original>».

1. Открой result/<имя>/extracted/text.txt и найди оглавление (обычно в первых 500–2000 строках).
2. Открой result/<имя>/extracted/pages/page-NNNN.png первых ~30 страниц, чтобы понять формат оглавления визуально.
3. Для каждой главы и каждого раздела внутри неё найди:
   - id (например, "1.3")
   - title_en (как в оригинале)
   - title_ru (короткий перевод)
   - lines [start, end] в text.txt
   - pages [start, end] в pages/
4. Запиши результат в JSON формата:

{
  "language": "<source_language>",
  "chapters": [
    {
      "number": 1,
      "slug": "01-essential-ideas",
      "title_en": "Essential Ideas",
      "title_ru": "Основные понятия",
      "lines": [120, 5200],
      "pages": [10, 60],
      "sections": [
        {"id": "1.1", "title_en": "…", "title_ru": "…", "lines": [120, 800], "pages": [10, 18]},
        …
      ]
    },
    …
  ]
}

Никаких переводов основного текста не делай. Сверяй диапазоны страниц с реальными PNG.
Если число страниц в JSON расходится с тем, что видишь — поправь.

Результат: обновлённый result/<имя>/translation/chapter_map.json.
```

---

## B. Переводчик раздела (запускается параллельно, 3–5 одновременно)

```
Прочитай perevodnik/CLAUDE.md, result/<имя>/translation/TRANSLATION_GUIDE.md,
result/<имя>/translation/DOMAIN.md и result/<имя>/translation/GLOSSARY.md.

Задание: перевести раздел <N.M> «<Section title EN>» главы <N>
книги «<title_original>» на <target_language>.

Источники (все пути относительно result/<имя>/):
  - Текст: extracted/text.txt, строки <line_start>–<line_end>.
  - Сканы: extracted/pages/page-<PPPP>.png … extracted/pages/page-<QQQQ>.png
    (источник истины для формул/таблиц/рисунков).
  - Глоссарий: translation/GLOSSARY.md (термины — только отсюда;
    новые добавляй в раздел Pending review).
  - Доменные правила: translation/DOMAIN.md.
  - Карта рисунков: translation/figure_map.json.

Результат:
  - Файл docs/chapters/<NN-slug>/section-<N>-<M>.md с frontmatter
    (см. TRANSLATION_GUIDE.md §7).
  - Рисунки, если есть, скопированы в docs/assets/figures/fig-<NN>-<MM>.<ext>.
  - Обновлены:
      translation/PROGRESS.md (раздел → [~]),
      translation/GLOSSARY.md (новые термины — в Pending review),
      translation/figure_map.json (новые соответствия).

Перед сдачей пройди чек-лист из §8 TRANSLATION_GUIDE.md.
status в frontmatter оставь "draft".
Не запускай mkdocs build, не делай git commit/push.
```

---

## C. Ревьюер раздела

```
Прочитай perevodnik/CLAUDE.md и result/<имя>/translation/TRANSLATION_GUIDE.md
(особенно §9). Также прочитай translation/DOMAIN.md и translation/GLOSSARY.md.

Задание: проверь раздел <N.M>,
файл result/<имя>/docs/chapters/<NN-slug>/section-<N>-<M>.md.

Сверь с оригиналом:
  - extracted/text.txt, строки <a>–<b>,
  - extracted/pages/page-<PPPP>.png … page-<QQQQ>.png.

Прогони чек-лист §8. Для каждого пункта — PASS / FAIL с пояснением.
Проверь термины по translation/GLOSSARY.md.
Посчитай количество примеров (Example), рисунков (Figure), таблиц (Table)
в оригинале и в переводе — они должны совпадать.

Если всё ок — поменяй в frontmatter status: draft → review
и в translation/PROGRESS.md [~] → [r] для этого раздела.
Если есть ошибки — НЕ исправляй сам, верни мне список FAIL.
```

---

## D. Сборщик главы (после того, как все разделы главы → review/done)

```
Прочитай perevodnik/CLAUDE.md и result/<имя>/translation/TRANSLATION_GUIDE.md (§10).

Задание: собери главу <N> книги «<title_original>».

Все пути ниже относительно result/<имя>/.

1. Проверь, что все docs/chapters/<NN-slug>/section-*.md имеют
   status review или done (и [r]/[x] в PROGRESS.md).
2. Создай или обнови docs/chapters/<NN-slug>/index.md — короткое введение
   из оригинала + автогенерированный список разделов (ссылки на section-*.md).
3. Запусти `python ../../core/scripts/render_mkdocs.py .` — обновит nav в mkdocs.yml
   из chapter_map.json.
4. Запусти `mkdocs build --strict`. Любая ошибка/предупреждение — стоп, опиши проблему.
5. После успешной сборки переведи [r] → [x] в PROGRESS.md для всех разделов главы.
6. Не делай git commit/push сам.
```

---

## E. Сопоставитель рисунков (опционально, фоном)

Если в книге много рисунков и их сопоставление вручную утомительно — отдельный проход.

```
Прочитай perevodnik/CLAUDE.md.

Задание: для каждого Figure N.M в главе <N> (см. result/<имя>/translation/chapter_map.json)
найди соответствующий файл в result/<имя>/extracted/images/. Действуй так:

  - Открой result/<имя>/extracted/pages/page-NNNN.png страниц главы.
  - Найди подпись 'Figure N.M' и визуально определи рисунок.
  - Сопоставь с extracted/images/img-XXX.{png,jpg}
    (они идут примерно в порядке появления в PDF).
  - Запиши в result/<имя>/translation/figure_map.json:
    "N.M": {
      "source": "extracted/images/img-XXX.png",
      "asset":  "docs/assets/figures/fig-NN-MM.png",
      "caption_en": "<подпись из PDF>"
    }
  - Скопируй файл в asset-путь (не перемещай, не удаляй из extracted/images/).

Никаких переводов и переименований оригинальных файлов в extracted/images/.
```

---

## Запуск параллельно

Чтобы не упереться в лимиты, запускай несколько переводчиков одновременно **одним сообщением** (несколько `Agent`-вызовов в одном ответе). Количество — из `book.yml: parallelism.translators` (по умолчанию 4). Больше не имеет смысла — потом всё равно ждать ревью.

**Порядок имеет значение:** сначала **Глава 1 целиком** одним пайплайном (картограф → переводчики 1.1…1.K параллельно → ревью → сборка). Глава 1 — эталон стиля и заодно «прогрев» глоссария. После неё запускай Главы 2–N параллельно.
