# Controlled Language: an agent skill for clear technical documentation in any language

**English** · [Русский](docs/ru/README.md) · [Other languages](docs/LANGUAGES.md)

**Controlled Language** is an open-source [Agent Skill](https://agentskills.io).
It makes an AI agent write, rewrite, and review technical documentation in a
controlled language, in English or in any other language. The rules come
from the principles of **ASD-STE100 Simplified Technical English** (STE), the
controlled language of aerospace maintenance manuals. You select how strict
the rules are: Level 1, 2, or 3.

- **English** is the native language of the approach. It gets the full rule
  set, and at Level 3 the approved vocabulary of ASD-STE100.
- **Other languages** get the same principles in a form that fits their
  grammar. Language files add rules for Russian, German, French, and
  Spanish. Native speakers can add more.

```bash
npx skills add amaklakov-droid/controlled-language-skill
```

The skill works with Claude, OpenAI Codex, GitHub Copilot, Cursor, Gemini
CLI, and other agents that support the `SKILL.md` standard. For chat models
without skill support, use the [system prompt](prompts/system-prompt.md).

> This project is not affiliated with or endorsed by ASD (Aerospace,
> Security and Defence Industries Association of Europe). ASD-STE100 is a
> trademark of ASD. The project does not contain the ASD-STE100 standard or
> its dictionary. See [Legal notice](#legal-notice).

## Why a controlled language

A controlled language limits the words and the sentence structures that a
writer can use. The result is text that has one meaning, that is fast to
read, and that is easy to translate. Readers who do not know the language
well understand it. Machine translation and LLMs process it with fewer
errors.

The idea for this skill came from a
[post by Andrej Karpathy](https://x.com/karpathy/status/2105819303471976479).
He asks LLMs to explain things in ASD-STE100, and sometimes asks for "80% of
the way" to it, because the full standard is strict. This skill makes
that approach repeatable: Level 2 is the "80%" level.

## What the skill does

| Mode | You give | You get |
| --- | --- | --- |
| Write | A topic, notes, code, or facts | A new document in a controlled language |
| Rewrite | Existing text or a file | The same content at the selected level, and notes |
| Review | Existing text or a file | A report with rule IDs, problems, and fixes |
| Respond | "Answer in controlled English" | Answers in a controlled language for the rest of the chat |

The skill changes only the prose. It keeps code, commands, file names, URLs,
UI labels, product names, and quotations as they are. It keeps the terms of
your project: names of components, data types, and domain actions.

## Levels

| | Level 1: Light | Level 2: Standard | Level 3: Strict |
| --- | --- | --- | --- |
| Share of rules | about 50% | about 80% (default) | 100% |
| Sentence length: instruction / description | 25 / 30 words | 20 / 25 words | 20 / 25 words |
| Vocabulary | Free, literal, specific | Simple common words, one meaning for each word | Only general words that ASD-STE100 approves, and your project terms |
| Grammar | Active voice, imperative steps | Also: no phrasal verbs, no "should" or "may" | Also: simple verb forms only, no "-ing" forms |
| Use for | Internal notes, a first cleanup | User guides, READMEs, API docs | Safety procedures, regulated products |

You can select the level in one of these places:

- the request: "rewrite this at Level 3";
- the front matter of a document;
- the project configuration file.

See [docs/en/levels.md](docs/en/levels.md).

## Languages

| | English | Other languages |
| --- | --- | --- |
| Rules | All 39 rules | 32 universal rules and the rules of the language file |
| Levels | 1, 2, 3 | 1, 2, 3 |
| Level 3 vocabulary | Only general words that ASD-STE100 approves | No vocabulary control: no approved dictionary exists |
| Language rules | Built in | [Russian](controlled-language/references/languages/ru.md), [German](controlled-language/references/languages/de.md), [French](controlled-language/references/languages/fr.md), [Spanish](controlled-language/references/languages/es.md) |

The universal rules control the structure. Examples are sentence length,
one instruction in each sentence, the condition first, active voice, one
term for each concept, and clear warnings. The language rules apply these ideas to the
grammar of each language. For example, the Russian rules replace «произведите
настройку» with «настройте».

For a language without a language file, the skill uses the universal rules
and tells you that the language has no file yet. To add a language, see
[docs/en/translating.md](docs/en/translating.md#language-rules-for-the-skill).

## Quick start

1. Install the skill (see [Installation](#installation)).
2. Ask your agent. For example:
   - "Rewrite `docs/install.md` in controlled English, Level 2."
   - "Review the README at Level 3 and give me a report."
   - "Write the upgrade procedure for this CLI. Use controlled English."
   - "Explain how OAuth works, 80% of the way to STE."
   - «Перепиши инструкцию `docs/ru/setup.md` понятным языком, уровень 3.»
3. Optional: add a configuration file to your project. Copy
   [`controlled-language.example.yml`](controlled-language/assets/controlled-language.example.yml)
   to `.controlled-language.yml` in the root folder. Write your terms in the
   glossary.

**Example (Level 2).**

Before:

<!-- controlled-language: off -->
> Once you've backed up your wallet, simply navigate to Settings and hit
> Upgrade - the app will then begin downloading the new version.
<!-- controlled-language: on -->

After:

> 1. Make a backup of your wallet.
> 2. Open the **Settings** page.
> 3. Click **Upgrade**.
>    The app downloads the new version.

More examples are in [examples/](examples/).

## Installation

The skill follows the open [Agent Skills](https://agentskills.io) standard.
The same folder works in each agent that supports `SKILL.md`.

| Agent | Command or location |
| --- | --- |
| Any agent (installer) | `npx skills add amaklakov-droid/controlled-language-skill` |
| Claude Code (plugin) | `/plugin marketplace add amaklakov-droid/controlled-language-skill`, then `/plugin install controlled-language@controlled-language-skill` |
| Claude.ai, Claude Desktop | Upload a ZIP of the `controlled-language/` folder in **Settings → Capabilities → Skills** |
| OpenAI Codex, GitHub Copilot, Cursor, Gemini CLI, OpenCode, Goose | `.agents/skills/controlled-language/` in the project, or the global skills folder of the agent |
| ChatGPT, Gemini, DeepSeek, local models | Paste [prompts/system-prompt.md](prompts/system-prompt.md) into the system prompt or the custom instructions |

The full instructions for each agent are in
[docs/en/installation.md](docs/en/installation.md).

## Checker script

The skill has a checker script. It finds the measurable problems: long
sentences, long paragraphs, semicolons, and the words from the word lists of
English and of the language files. For English, it also finds passive
voice, phrasal verbs, "-ing" forms, and unclear obligation words. It finds
the language of each file automatically. It needs only Python 3.8 or later.

```bash
python3 controlled-language/scripts/check.py --level 2 README.md docs/
```

You can use it in continuous integration (CI) with
`--fail-on violation`. The checker does not understand meaning, so it
cannot replace the review of a person or of the skill. See [docs/en/usage.md](docs/en/usage.md#checker-script).

## Repository structure

```
controlled-language/             The skill
├── SKILL.md                     Workflow, languages, levels, rules at a glance, output
├── references/
│   ├── rules.md                 Rule catalog: 39 rules, strength for each level
│   ├── languages.md             How the skill works with each language
│   ├── languages/               Language files: ru, de, fr, es, and a template
│   ├── word-choices.md          English words to avoid and their replacements
│   ├── configuration.md         Project file, front matter, markers
│   └── examples.md              Calibration examples for each level
├── scripts/check.py             Checker script (Python, no dependencies)
└── assets/
    └── controlled-language.example.yml
prompts/system-prompt.md         One-file version for chat models without skills
docs/en/                         Documentation (English, the source)
docs/ru/                         Documentation (Russian)
docs/LANGUAGES.md                Status of the translations
examples/                        Before-and-after examples
tools/i18n_status.py             Translation status tool
.claude-plugin/                  Claude Code plugin and marketplace manifests
```

## Documentation

- [Installation](docs/en/installation.md): each agent, step by step.
- [Usage](docs/en/usage.md): modes, prompts, the checker script, and CI.
- [Levels](docs/en/levels.md): what changes at each level, and how to select
  a level.
- [Configuration](docs/en/configuration.md): the project file, the glossary,
  front matter, and markers.
- [Translating](docs/en/translating.md): how to add a language to the
  documentation and to the skill.

## Contributing

Contributions are welcome. You can fix the documentation, add a language,
report a bad output of the skill, or improve the checker. Read
[CONTRIBUTING.md](CONTRIBUTING.md).

**Languages.** Native speakers can help in two ways:

- translate the documentation;
- write or review the language file of the skill for their language.

To start, open a
[language request](https://github.com/amaklakov-droid/controlled-language-skill/issues/new?template=language-request.yml).
An AI makes the first draft. Then native speakers review it. Then we publish
it. See [docs/en/translating.md](docs/en/translating.md).

## Legal notice

- **License.** This project is licensed under the
  [Apache License 2.0](LICENSE). See also [NOTICE](NOTICE).
- **Trademark.** ASD-STE100 Simplified Technical English is a copyright and
  a trademark of ASD (Aerospace, Security and Defence Industries Association
  of Europe), Brussels. EU Trade Mark No. 017966390. This project uses the
  name only to refer to the standard.
- **No affiliation.** ASD and its Simplified Technical English Maintenance
  Group (STEMG) did not make, approve, or certify this project. Text that you
  make with this skill is not certified as compliant with ASD-STE100.
- **No standard text.** The project does not contain the text or the
  dictionary of ASD-STE100. The rules here are an original description of
  the principles of controlled technical English.
- **The official standard.** ASD gives the standard free of charge on
  request at [asd-ste100.org](https://www.asd-ste100.org/). Use it for
  formal compliance work.

## Acknowledgments

- [Andrej Karpathy](https://x.com/karpathy/status/2105819303471976479), for
  the idea to ask LLMs for ASD-STE100 and for "80% of the way" to it.
- The ASD STEMG, for decades of work on ASD-STE100 and for the free access
  to the standard.
