# Configuration

**English** · [Русский](../ru/configuration.md)

You can control the skill in three ways:

1. A project configuration file: `.controlled-language.yml`.
2. A setting in the front matter of a document.
3. Markers in the text.

All three are optional. Without them, the skill uses Level 2 and finds the
terms of your project in the context.

## Contents

- [Project configuration file](#project-configuration-file)
- [Fields](#fields)
- [Glossary](#glossary)
- [Front matter](#front-matter)
- [Markers](#markers)
- [Precedence](#precedence)

## Project configuration file

1. Copy
   [`controlled-language.example.yml`](../../controlled-language/assets/controlled-language.example.yml)
   to the root folder of your project.
2. Change the name of the file to `.controlled-language.yml`.
3. Delete the fields that you do not need.
4. Write your terms in the `glossary`.

A minimal file:

```yaml
level: 2
glossary:
  technical_nouns: [API key, webhook, dashboard]
```

A complete file:

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

The skill and the checker script read the same file.

## Fields

| Field | Values | Default | Description |
| --- | --- | --- | --- |
| `level` | 1, 2, 3 | 2 | The default level of the project. |
| `spelling` | `us`, `uk` | `us` | The spelling for Levels 1 and 2. Level 3 always uses `us`. |
| `include` | list of globs | all text files | The files that the rules apply to. |
| `exclude` | list of globs | none | The files that the rules do not apply to. `exclude` is stronger than `include`. |
| `overrides` | list of `path` and `level` | none | Levels for some paths. The first match applies. |
| `glossary.technical_nouns` | list | none | Names of things in your domain. |
| `glossary.technical_verbs` | list | none | Actions of your domain. |
| `glossary.preferred_terms` | list of `use` and `not` | none | One term for each concept. The skill replaces each `not` form with the `use` form. |
| `avoid_words` | list of `word` and `use` | none | Words that your project does not want. |
| `keep_verbatim` | list | none | Strings that the skill never changes. |
| `language` | `auto`, a language code | `auto` | The language of the documents. With `auto`, the skill and the checker find the language of each file. |
| `non_english` | `apply`, `off` | `apply` | What to do with text that is not in English. `apply` uses the universal rules and the language file. `off` does not change the text. |

The file uses a simple subset of YAML: keys, lists, nested keys, and inline
lists (`[a, b]`). The checker script reads this subset without extra
packages.

## Glossary

ASD-STE100 lets writers use the terms of their subject. It calls them
**technical nouns** and **technical verbs**. The vocabulary rules do not
apply to these terms.

- **Technical nouns** are names of things: products, components, screens, UI
  elements, data types, files, tools. Examples: "API key", "webhook",
  "Settings page", "smart contract".
- **Technical verbs** are actions of your domain that have no simple
  general word. Examples: "deploy", "commit", "click", "download", "sign" (a
  transaction).
- **Preferred terms** make sure that one concept has one name. If your team
  writes "log in", "login", and "sign in" for the same action, select one.

Each term counts as one word for the sentence length.

Good glossary terms:

- are the names that the product UI and the code use;
- have one meaning in your documentation;
- are as short as possible.

Do not put general words into the glossary only to make them acceptable at
Level 3. For example, "utilize" is not a term.

## Front matter

Set the level for one document in its front matter:

```markdown
---
title: Recover a wallet
controlled-language: 3
---
```

The long form also works:

```markdown
---
controlled-language:
  level: 3
---
```

To give the language of a document, add `lang` to the front matter. Use
this when the automatic language detection is wrong:

```markdown
---
lang: ru
controlled-language: 3
---
```

## Markers

Use HTML comments to control a part of a document.

Turn the rules off and on:

```markdown
<!-- controlled-language: off -->
This paragraph is a quotation from the license and stays as it is.
<!-- controlled-language: on -->
```

Change the level from this point:

```markdown
<!-- controlled-language: level 3 -->
WARNING: Disconnect the power cable before you open the case.
<!-- controlled-language: level 2 -->
```

Markdown viewers do not show HTML comments, so the markers are not visible
to readers.

## Precedence

When two settings give different levels, the skill uses the first one in
this list:

1. The level in the request.
2. A marker in the text (for the text after the marker).
3. The front matter of the document.
4. The first `overrides` entry that matches the path.
5. The `level` field of the configuration file.
6. Level 2.

For the checker script, the `--level` option is the "request".
