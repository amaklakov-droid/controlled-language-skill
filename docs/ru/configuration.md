<!--
i18n:
  source: docs/en/configuration.md
  source_hash: 5a2dc047c61f
  status: reviewed
  translated_with: ai
  reviewed_by: [@amaklakov-droid]
-->

# Конфигурация

[English](../en/configuration.md) · **Русский**

Управлять skill можно тремя способами:

1. Конфигурационный файл проекта `.controlled-language.yml`.
2. Настройка во front matter документа.
3. Маркеры в тексте.

Все три способа необязательны. Без них skill использует уровень 2 и сам
находит термины проекта в контексте.

## Содержание

- [Конфигурационный файл проекта](#конфигурационный-файл-проекта)
- [Поля](#поля)
- [Глоссарий](#глоссарий)
- [Front matter](#front-matter)
- [Маркеры](#маркеры)
- [Приоритет настроек](#приоритет-настроек)

## Конфигурационный файл проекта

1. Скопируйте
   [`controlled-language.example.yml`](../../controlled-language/assets/controlled-language.example.yml)
   в корень проекта.
2. Переименуйте файл в `.controlled-language.yml`.
3. Удалите ненужные поля.
4. Впишите свои термины в `glossary`.

Минимальный файл:

```yaml
level: 2
glossary:
  technical_nouns: [API key, webhook, dashboard]
```

Полный файл:

```yaml
level: 2
spelling: us

include:
  - "README.md"
  - "docs/**/*.md"
exclude:
  - "CHANGELOG.md"
  - "docs/legal/**"

overrides:
  - path: "docs/safety/**"
    level: 3
  - path: "blog/**"
    level: 1

glossary:
  technical_nouns:
    - API key
    - smart contract
  technical_verbs:
    - deploy
    - sign
  preferred_terms:
    - use: sign in
      not: [log in, login, log on]

avoid_words:
  - word: seamless
    use: (delete the word)

keep_verbatim:
  - "Terms of Service"

language: auto
non_english: apply
```

Skill и скрипт проверки читают один и тот же файл.

## Поля

| Поле | Значения | По умолчанию | Описание |
| --- | --- | --- | --- |
| `level` | 1, 2, 3 | 2 | Уровень проекта по умолчанию. |
| `spelling` | `us`, `uk` | `us` | Орфография для уровней 1 и 2. Уровень 3 всегда использует `us`. |
| `include` | список glob-шаблонов | все текстовые файлы | Файлы, к которым применяются правила. |
| `exclude` | список glob-шаблонов | нет | Файлы, к которым правила не применяются. `exclude` сильнее `include`. |
| `overrides` | список `path` и `level` | нет | Уровни для отдельных путей. Действует первое совпадение. |
| `glossary.technical_nouns` | список | нет | Названия объектов вашей предметной области. |
| `glossary.technical_verbs` | список | нет | Действия вашей предметной области. |
| `glossary.preferred_terms` | список `use` и `not` | нет | Один термин для одного понятия. Skill заменяет каждую форму из `not` на форму из `use`. |
| `avoid_words` | список `word` и `use` | нет | Слова, которые проект не хочет видеть. |
| `keep_verbatim` | список | нет | Строки, которые skill никогда не меняет. |
| `language` | `auto`, код языка | `auto` | Язык документов. При `auto` skill и скрипт проверки определяют язык каждого файла. |
| `non_english` | `apply`, `off` | `apply` | Что делать с текстом не на английском. `apply` — применять универсальные правила и языковой файл. `off` — не менять текст. |

Файл использует простое подмножество YAML: ключи, списки, вложенные ключи и
списки в строку (`[a, b]`). Скрипт проверки читает это подмножество без
дополнительных пакетов.

## Глоссарий

ASD-STE100 разрешает использовать термины предметной области. Стандарт
называет их **technical nouns** (технические существительные) и **technical
verbs** (технические глаголы). Правила словаря на эти термины не
распространяются.

- **Технические существительные** — названия объектов: продуктов,
  компонентов, экранов, элементов интерфейса, типов данных, файлов,
  инструментов. Примеры: «API key», «webhook», «Settings page», «smart
  contract».
- **Технические глаголы** — действия предметной области, для которых нет
  простого общего слова. Примеры: «deploy», «commit», «click», «download»,
  «sign» (транзакцию).
- **Предпочтительные термины** закрепляют одно название за одним понятием.
  Если в команде пишут и «log in», и «login», и «sign in» об одном и том же
  действии, выберите один вариант.

Каждый термин считается одним словом при подсчёте длины предложения.

Хорошие термины глоссария:

- совпадают с названиями в интерфейсе и коде продукта;
- имеют одно значение в вашей документации;
- максимально короткие.

Не вносите в глоссарий общие слова только для того, чтобы они стали
допустимы на уровне 3. Например, «utilize» — не термин.

## Front matter

Уровень для одного документа задаётся в его front matter:

```markdown
---
title: Recover a wallet
controlled-language: 3
---
```

Работает и полная форма:

```markdown
---
controlled-language:
  level: 3
---
```

Чтобы указать язык документа, добавьте во front matter поле `lang`. Это
нужно, если автоматическое определение языка ошиблось:

```markdown
---
lang: ru
controlled-language: 3
---
```

## Маркеры

HTML-комментарии управляют частью документа.

Выключить и включить правила:

```markdown
<!-- controlled-language: off -->
This paragraph is a quotation from the license and stays as it is.
<!-- controlled-language: on -->
```

Изменить уровень начиная с этого места:

```markdown
<!-- controlled-language: level 3 -->
WARNING: Disconnect the power cable before you open the case.
<!-- controlled-language: level 2 -->
```

Программы просмотра Markdown не показывают HTML-комментарии, поэтому
читатели маркеров не видят.

## Приоритет настроек

Если две настройки задают разные уровни, skill использует первую по этому
списку:

1. Уровень в запросе.
2. Маркер в тексте (для текста после маркера).
3. Front matter документа.
4. Первое подходящее правило `overrides`.
5. Поле `level` конфигурационного файла.
6. Уровень 2.

Для скрипта проверки «запрос» — это параметр `--level`.
