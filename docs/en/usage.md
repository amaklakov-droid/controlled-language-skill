# Usage

**English** · [Русский](../ru/usage.md)

This page shows how to use the skill in each mode and how to select a
level. It also shows how to use the checker script in continuous
integration (CI).

## Contents

- [How the skill starts](#how-the-skill-starts)
- [Modes](#modes)
- [Select the level](#select-the-level)
- [Project terms](#project-terms)
- [What the skill does not change](#what-the-skill-does-not-change)
- [Text in other languages](#text-in-other-languages)
- [Checker script](#checker-script)
- [Use in CI](#use-in-ci)
- [Limits](#limits)

## How the skill starts

Most agents start the skill automatically when the request is about clear
technical English, documentation, or ASD-STE100. You can also start it
directly:

- In Claude Code: `/controlled-language <request>`.
- In other agents: write "Use the controlled-language skill" in the request.

## Modes

### Write

Give the topic and the facts. The skill writes a new document.

```
Write the installation guide for our CLI in controlled English.
Facts: Node.js 20 or later. Install with `npm i -g acme-cli`.
Run `acme login` once. The config is in ~/.acme/config.json.
```

### Rewrite

Give the text or the file. The skill changes the prose to the level and
keeps the facts.

```
Rewrite docs/upgrade.md at Level 2. Edit the file in place.
```

After the text, the skill gives a short "Notes" block:

- the level and its source;
- glossary candidates (the terms that it found);
- words to verify (Level 3 only);
- questions (for example, a value that the original does not give).

### Review

Give the text or the file. The skill gives a report. Each row has a line
number, a rule ID, the problem, and a fix.

```
Review README.md at Level 3. Do not change the file.
```

The report has three types of findings:

| Type | Meaning |
| --- | --- |
| Violation | The text breaks a "must" rule of the level. |
| Warning | The text possibly breaks a rule. A person must decide. |
| Suggestion | The text does not follow a "prefer" rule of the level. |

### Respond

Ask the agent to answer in controlled English. The mode stays on until you
stop it.

```
From now on, answer in controlled English, Level 2.
Explain how database indexes work.
```

## Select the level

Write the level in the request:

| You write | Level |
| --- | --- |
| "Level 1", "light", "relaxed", "50%" | 1 |
| "Level 2", "standard", "80% of the way to ASD-STE100" | 2 |
| "Level 3", "strict", "full STE", "100%" | 3 |

If the request does not give a level, the skill uses the level from the
document front matter, then from the project configuration file. The
default is Level 2. See [levels.md](levels.md) and
[configuration.md](configuration.md).

## Project terms

Your project has its own words: names of components, screens, data types,
and actions. The skill does not simplify them. It uses each term in the same
form every time.

For the best results, write your terms in the glossary of
`.controlled-language.yml`:

```yaml
glossary:
  technical_nouns: [API key, webhook, dashboard]
  technical_verbs: [deploy, sign]
  preferred_terms:
    - use: sign in
      not: [log in, login]
```

If there is no glossary, the skill finds the terms in the context. In
rewrite and review modes, it lists them as "Glossary candidates". Copy the
correct ones into the glossary.

## What the skill does not change

The skill applies the rules only to prose. It does not change:

- code blocks, inline code, and commands;
- file names, paths, URLs, and e-mail addresses;
- names of APIs, functions, variables, and fields;
- UI labels (the skill keeps the exact capitalization);
- product names and the `keep_verbatim` strings of the configuration file;
- quotations, legal text, and text between `off` markers.

## Text in other languages

The skill works with text in any language. English is the native language
of the approach. For other languages, the skill applies:

- the 32 universal rules, for example short sentences, the condition first,
  active voice, and one term for each concept;
- the rules of the language file, if the language has one.

Language files exist for Russian, German, French, and Spanish. For example,
the Russian file replaces «произведите настройку» with «настройте» and
removes adverbial-participle clauses. See
[languages.md](../../controlled-language/references/languages.md).

All three levels work in all languages. Level 3 in other languages makes
all rules "must", but it does not control the vocabulary. ASD-STE100 has an
approved dictionary only for English.

The skill finds the language of the text. You can also give the language
yourself in one of these places:

- the request;
- the front matter of the document: `lang: ru`;
- the `language` field of the configuration file. To leave text in other languages
unchanged, set `non_english: off`.

## Checker script

The checker script finds the measurable problems in a text. It needs Python
3.8 or later and no other packages.

```bash
python3 controlled-language/scripts/check.py [options] PATH [PATH ...]
```

`PATH` is a file, a folder, or `-` (the standard input). In a folder, the
checker reads `.md`, `.mdx`, `.markdown`, and `.txt` files.

| Option | Description |
| --- | --- |
| `--level {1,2,3}` | Use this level for all files. Without it, the checker uses the front matter, the configuration file, or Level 2. |
| `--config PATH` | Use this configuration file. Without it, the checker looks for `.controlled-language.yml` in the current folder and in the folders above it. |
| `--format {text,json}` | The output format. The default is `text`. |
| `--fail-on {never,violation,warning}` | Exit with code 1 if the checker finds a violation (or a violation or a warning). The default is `never`. |
| `--no-suggestions` | Do not show suggestions. |
| `--lang CODE` | The language of the text: `auto` (the default), `en`, or a language code such as `ru`, `de`, or `pt-BR`. `auto` finds the language of each file. |
| `--word-list PATH` | Use a different English word list. |
| `--languages-dir PATH` | Use the language files in this folder. |

Example output:

```
docs/install.md:12: violation S2 Sentence has 27 words (max 20 in an instruction at Level 2) — "Open the terminal, go to the project folder and…"
docs/install.md:15: warning V1 Passive voice: "is read" — "The file is read at startup."
docs/install.md: Level 2 (config), en, 41 sentences (18 procedural, 23 descriptive): 3 violations, 2 warnings, 4 suggestions, 7.3 violations per 100 sentences
```

**What the checker finds in all languages:**

- long sentences (S2) and long paragraphs (D2);
- semicolons (S5);
- the words of the word table of the language file (for example, RU2 and
  RU3 in Russian);
- the `avoid_words` and `preferred_terms` of your project;
- safety text in notes (SF2), with the signal words of the language file.

The checker does not count the length of sentences in Chinese, Japanese,
and Thai, because these languages do not use spaces between words.

**What the checker also finds in English:**

- passive voice (V1);
- perfect and continuous tenses (V2);
- phrasal verbs (V3);
- "-ing" forms (W6);
- words from the [English word list](../../controlled-language/references/word-choices.md);
- abbreviations without a definition (W9);
- UK or US spelling (W8);
- instructions in notes (P5);
- warnings that do not start with a command (SF1);
- double negatives (S6).

**What the checker does not find:** meaning problems. For example:

- a word with a second meaning;
- a vague statement that has no vague word;
- a long noun cluster;
- a step in the wrong order.

Use the review mode of the skill for these problems.

## Use in CI

Add the checker to your CI pipeline. This GitHub Actions job checks the
documentation at Level 2 and stops the build if it finds a violation:

```yaml
name: Docs style
on: [pull_request]
jobs:
  controlled-language:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/checkout@v4
        with:
          repository: amaklakov-droid/controlled-language-skill
          path: .controlled-language-skill
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: >
          python .controlled-language-skill/controlled-language/scripts/check.py
          --fail-on violation README.md docs/
```

Start with `--fail-on never` on an old documentation set. Fix the
violations, and then change the option to `--fail-on violation`.

## Limits

- The skill and the checker help writers. They do not replace a trained
  editor.
- Level 3 relies on the knowledge of the model about the approved
  vocabulary of ASD-STE100. The project does not contain the dictionary.
  The skill lists the words that it is not sure about.
- Text from this skill is not certified as compliant with ASD-STE100. For
  formal compliance, review the text against the
  [official standard](https://www.asd-ste100.org/).
