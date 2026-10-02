<!--
i18n:
  source: docs/en/installation.md
  source_hash: 234ae7bb62f5
  status: draft
  translated_with: ai
  reviewed_by: []
-->

# Установка

[English](../en/installation.md) · **Русский**

Skill — это папка `controlled-language/`. В ней лежат `SKILL.md` и
справочные файлы. Папка соответствует открытому стандарту
[Agent Skills](https://agentskills.io), поэтому работает во всех агентах,
которые поддерживают `SKILL.md`.

Выберите агент:

- [Любой агент: установщик `skills`](#любой-агент-установщик-skills)
- [Claude Code](#claude-code)
- [Claude.ai и Claude Desktop](#claudeai-и-claude-desktop)
- [Claude API и Claude Agent SDK](#claude-api-и-claude-agent-sdk)
- [OpenAI Codex, GitHub Copilot, Cursor, Gemini CLI и другие агенты](#openai-codex-github-copilot-cursor-gemini-cli-и-другие-агенты)
- [Чат-модели без поддержки skills](#чат-модели-без-поддержки-skills)

После установки [проверьте](#проверка-установки), что skill работает.

## Любой агент: установщик `skills`

[CLI `skills`](https://github.com/vercel-labs/skills) устанавливает skill
в выбранные агенты. Нужен Node.js 18 или новее.

```bash
npx skills add amaklakov-droid/controlled-language-skill
```

Установщик спросит, в какие агенты ставить skill. Чтобы установить skill
для всех проектов и одного агента (например, Codex), добавьте параметры:

```bash
npx skills add amaklakov-droid/controlled-language-skill -g -a codex
```

## Claude Code

### Как плагин

Добавьте репозиторий как маркетплейс плагинов. Затем установите плагин.
Введите в Claude Code:

```
/plugin marketplace add amaklakov-droid/controlled-language-skill
/plugin install controlled-language@controlled-language-skill
```

Для обновления введите `/plugin marketplace update controlled-language-skill`.

### Как папку

1. Клонируйте репозиторий:

   ```bash
   git clone https://github.com/amaklakov-droid/controlled-language-skill.git
   ```

2. Скопируйте папку skill в личную папку skills:

   ```bash
   mkdir -p ~/.claude/skills
   rm -rf ~/.claude/skills/controlled-language
   cp -R controlled-language-skill/controlled-language ~/.claude/skills/controlled-language
   ```

   Чтобы skill работал только в одном проекте, скопируйте папку
   в `<проект>/.claude/skills/`.

> Примечание: указывайте имя папки назначения полностью, как в команде выше.
> В macOS `cp` копирует только содержимое папки, если путь источника
> заканчивается на `/`.

Skill можно вызвать напрямую: `/controlled-language rewrite README.md at
Level 3`.

## Claude.ai и Claude Desktop

1. Создайте ZIP-архив папки `controlled-language/`. Файл `SKILL.md` должен
   лежать в корне папки внутри архива.

   ```bash
   cd controlled-language-skill
   zip -r controlled-language.zip controlled-language
   ```

2. Откройте **Settings → Capabilities → Skills**.
3. Нажмите **Upload skill** и выберите `controlled-language.zip`.

Скрипту проверки нужно выполнение кода. Если выполнение кода выключено,
skill работает без скрипта.

## Claude API и Claude Agent SDK

- **Claude API**: загрузите папку `controlled-language/` через
  [Skills API](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview).
  Затем подключите skill к контейнеру запроса.
- **Claude Agent SDK**: скопируйте папку в `.claude/skills/` рабочей папки
  агента. Затем включите настройку skills в SDK.

## OpenAI Codex, GitHub Copilot, Cursor, Gemini CLI и другие агенты

Эти агенты читают skills из общей папки проекта `.agents/skills/`. У каждого
агента есть и своя глобальная папка.

**Один проект.** Скопируйте папку skill в `.agents/skills/` проекта:

```bash
mkdir -p .agents/skills
cp -R controlled-language-skill/controlled-language .agents/skills/controlled-language
```

**Все проекты.** Скопируйте папку skill в глобальную папку агента:

| Агент | Глобальная папка |
| --- | --- |
| OpenAI Codex | `~/.codex/skills/` |
| GitHub Copilot | `~/.copilot/skills/` |
| Cursor | `~/.cursor/skills/` |
| Gemini CLI | `~/.gemini/skills/` |
| OpenCode | `~/.config/opencode/skills/` |
| Goose | `~/.config/goose/skills/` |

Например, для Codex:

```bash
mkdir -p ~/.codex/skills
cp -R controlled-language-skill/controlled-language ~/.codex/skills/controlled-language
```

Некоторые агенты читают и свои папки проекта, например `.github/skills/`
(GitHub Copilot). Если вашего агента нет в списке, откройте его
документацию. Ищите «Agent Skills» или «SKILL.md». Установщик `skills` знает
папки многих агентов.

## Чат-модели без поддержки skills

ChatGPT, Gemini, DeepSeek, Mistral и локальные модели не читают файлы
`SKILL.md`. Используйте версию skill в одном файле:

1. Откройте [prompts/system-prompt.md](../../prompts/system-prompt.md).
2. Скопируйте текст между строками `--- BEGIN PROMPT ---` и
   `--- END PROMPT ---`.
3. Вставьте текст в одно из мест:
   - **ChatGPT**: custom GPT (Instructions), Project (Instructions) или
     **Settings → Personalization → Custom instructions**.
   - **Gemini**: Gem (Instructions).
   - **API или локальная модель**: системный промпт.
4. Измените строку `Default level: 2`, если нужен другой уровень
   по умолчанию.

Для длинных документов приложите к диалогу ещё и файл
[`references/rules.md`](../../controlled-language/references/rules.md).

## Проверка установки

Начните новую сессию агента и отправьте запрос:

```
Rewrite this text in controlled English, Level 2:
"Once the migration has been completed, you should simply restart the
service in order to apply the changes."
```

Правильный ответ похож на этот:

> After the migration is complete, restart the service to apply the changes.

Ответ также называет уровень и его источник, например «Level 2 (request)».
Если агент не использует skill, напишите в запросе «Use the
controlled-language skill». Затем проверьте расположение папки.

## Обновление и удаление

- **Установщик `skills`**: обновление — `npx skills update
  controlled-language`, удаление — `npx skills remove controlled-language`.
- **Плагин Claude Code**: обновление — `/plugin marketplace update
  controlled-language-skill`, удаление — `/plugin uninstall
  controlled-language`.
- **Копия папки**: выполните `git pull` в клоне репозитория и скопируйте
  папку снова. Чтобы удалить skill, удалите папку.
