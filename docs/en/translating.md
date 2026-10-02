# Translate the documentation

**English** · [Русский](../ru/translating.md)

This page tells you how to add a language to the documentation and how to
keep a translation current. It also tells you how to add the rules of a
language to the skill. It is for translators, reviewers, and the
maintainer.

Native speakers can help in two ways:

- translate the documentation (the main part of this page);
- write or review the language file of the skill (see
  [Language rules for the skill](#language-rules-for-the-skill)).

English is the source language. The English files are the reference for all
translations. An AI model makes the first draft of a translation. Then native
speakers review the draft. After the review, the maintainer publishes the
translation.

## Contents

- [Roles](#roles)
- [Files and folders](#files-and-folders)
- [The i18n header](#the-i18n-header)
- [The process](#the-process)
  - [Step 1: Request a language](#step-1-request-a-language)
  - [Step 2: Accept the language](#step-2-accept-the-language)
  - [Step 3: Make the AI draft](#step-3-make-the-ai-draft)
  - [Step 4: Open a pull request](#step-4-open-a-pull-request)
  - [Step 5: Review the translation](#step-5-review-the-translation)
  - [Step 6: Stamp the translation as reviewed](#step-6-stamp-the-translation-as-reviewed)
  - [Step 7: Merge and publish](#step-7-merge-and-publish)
  - [Step 8: Keep the translation current](#step-8-keep-the-translation-current)
- [Glossary](#glossary)
- [What not to translate](#what-not-to-translate)
- [Disagreements between reviewers](#disagreements-between-reviewers)
- [Become a language maintainer](#become-a-language-maintainer)
- [Language rules for the skill](#language-rules-for-the-skill)
- [Tool reference](#tool-reference)

## Roles

| Role | Who | Tasks |
| --- | --- | --- |
| Requester | Any person | Asks for a new language. |
| Translator | Any person | Makes the draft with an AI model or by hand. Updates the translation when the English source changes. |
| Reviewer | A native speaker of the language | Compares the translation with the English source. Approves the translation or proposes changes. |
| Language maintainer | An experienced reviewer | Owns the folder of the language. Keeps the glossary current. |
| Maintainer | [@amaklakov-droid](https://github.com/amaklakov-droid) | Accepts new languages. Merges pull requests. Makes the final decision in a disagreement. |

One person can have more than one role. But a reviewer cannot approve a
pull request that they opened. GitHub does not let the author of a pull
request approve it.

## Files and folders

Each language has a folder in `docs/`. The name of the folder is the
language code. Use a code in the Best Current Practice 47 (BCP 47) format, for example `ru`, `de`, or `pt-BR`.

| English source | Translation |
| --- | --- |
| `README.md` | `docs/<lang>/README.md` |
| `docs/en/<name>.md` | `docs/<lang>/<name>.md` |

A translation has the same file name as its English source.
[LANGUAGES.md](../LANGUAGES.md) shows the status of each language.

## The i18n header

Each translation starts with an i18n header. "i18n" is a short form of
"internationalization". The header is an HTML comment, so GitHub does not
show it on the page.

```markdown
<!--
i18n:
  source: docs/en/usage.md
  source_hash: 1a2b3c4d5e6f
  status: draft
  translated_with: ai
  reviewed_by: []
-->
```

| Field | Value |
| --- | --- |
| `source` | The path of the English source from the repository root. For a file that is not a translation, use `none` (see [Glossary](#glossary)). |
| `source_hash` | The first 12 characters of the SHA-256 hash of the English source. The tool calculates the hash. Do not edit it by hand. |
| `status` | `draft`: the translation waits for a review. `reviewed`: a reviewer approved the translation. |
| `translated_with` | `ai`: an AI model made the first draft. `human`: a person made the first draft. |
| `reviewed_by` | The GitHub handles of the reviewers, for example `[@amaklakov-droid]`. |

Do not write the header by hand. Use the `stamp` command of
`tools/i18n_status.py` (see [Tool reference](#tool-reference)). To stamp a
file means to write or refresh its header with this command.

The tool compares `source_hash` with the hash of the current English source.
Then it gives each file one of these states:

| State | Meaning |
| --- | --- |
| `current` | The translation matches the current English source. |
| `outdated` | The English source changed after the last stamp. The translation needs an update. |
| `missing` | The language folder has no file for an English source. |
| `untranslated` | The file is still the English copy that the `new` command made. |
| `invalid` | The file has no header, or the header has an error. |
| `standalone` | The file is not a translation (`source: none`). The tool does not count it. |

## The process

The process has eight steps. Each step has a section below.

### Step 1: Request a language

Any person can request a new language.

1. Open the form
   [Request a documentation language](https://github.com/amaklakov-droid/controlled-language-skill/issues/new?template=language-request.yml).
2. Write the name of the language and its BCP 47 code.
3. Write who will read the documentation in this language.
4. Tell us if you can review the translation as a native speaker.
5. If you know other possible reviewers, write their GitHub handles.
6. Submit the issue.

The maintainer accepts a language only if at least one native speaker agrees
to review the translation. If you are not a native speaker, find a reviewer
first. You can ask for reviewers in
[Discussions](https://github.com/amaklakov-droid/controlled-language-skill/discussions).

### Step 2: Accept the language

The maintainer does these steps:

1. Add the label `lang:<lang>` to `.github/labels.yml`.
2. Run `tools/sync_labels.sh` to create the label on GitHub.
3. Add the label `lang:<lang>` to the request.
4. Make the language folder:

   ```bash
   python3 tools/i18n_status.py new <lang>
   ```

   The command copies each English source to `docs/<lang>/`. It adds an i18n
   header with `status: draft` to each copy.
5. Add the folder `docs/<lang>/**` to `.github/labeler.yml`. Add it to the
   `i18n` label and to a new `lang:<lang>` label.
6. Add the folder and its reviewers to `.github/CODEOWNERS`:

   ```text
   /docs/<lang>/ @amaklakov-droid @reviewer-handle
   ```

7. Add the reviewers to the reviewer list in [LANGUAGES.md](../LANGUAGES.md).

A translator who works in a fork can also run the `new` command in the fork.
The maintainer then does the other steps in a separate pull request.

### Step 3: Make the AI draft

The translator makes the draft. Do these steps for each file in
`docs/<lang>/`:

1. Open the file. After the header, the file contains the English text.
2. Copy the AI prompt below into your AI model.
3. Replace the placeholders in curly brackets in the prompt.
4. Paste the content of the file at the end of the prompt.
5. Replace the content of the file with the result.
6. Make sure that the header did not change.

```text
Translate the Markdown file below from English into {LANGUAGE} ({CODE}).
The file is part of the documentation of "controlled-language", an agent
skill for technical writing.

Rules:
1. Keep the Markdown structure: headings, lists, tables, block quotes,
   blank lines, and HTML comments.
2. Keep the i18n header (the first HTML comment, which starts with "i18n:")
   exactly as it is.
3. Do not translate code blocks, inline code, commands, options, file
   names, paths, configuration keys, URLs, rule IDs (for example S2 or V3),
   or product names.
4. Keep the target of each link. Translate only the link text. If a link
   goes to a heading (the part after "#"), change that part to match the
   translated heading. GitHub makes this part from the heading text: lower
   case, hyphens in place of spaces, and no punctuation.
5. Keep UI labels in English when the product UI is in English.
6. Keep English example sentences that show the rules of controlled English
   in English. They are examples of English text.
7. In the language bar (the line of language links under the first
   heading), show {LANGUAGE} in bold without a link. Make "English" a link
   to the English page.
8. Translate all other text. For instructions, use the standard imperative
   form of {LANGUAGE} for technical documentation.
9. Write short sentences. Give one instruction in each sentence. If an
   English sentence is long, make two sentences.
10. Use one term for each concept in all files. Use the terms of the
    glossary. Do not use synonyms to make the text less repetitive.
11. Do not add, remove, or explain content. Do not add notes.
12. Do not write that the project is compliant with ASD-STE100, certified,
    or endorsed by ASD.
13. Output only the translated file. Do not put it in a code block.

Glossary (English term: {LANGUAGE} term):
{GLOSSARY}

File {FILE}:
```

Use the prompt in English for all languages. Replace `{GLOSSARY}` with the
table from `docs/<lang>/glossary.md`. If the language has no glossary yet,
write `none`.

You can also translate a file by hand. Then stamp the file with
`--translated-with human` before you open the pull request.

**Review the draft with the skill.** Use the controlled-language skill at
Level 2 to review the draft. For text that is not in English, the skill
applies the universal rules and the language file of the language, if the
file exists. For example, give this request to your agent:

```text
Use the controlled-language skill at Level 2.
Review docs/<lang>/usage.md. The text is in <language>. Do not change code,
links, or the i18n header.
```

Correct the problems that the review finds. Do not change the meaning of the
text.

**Examine the status.** Run this command:

```bash
python3 tools/i18n_status.py check
```

Each file of the language must show `draft` and `current`. If a file shows
`untranslated`, the file still contains the English text.

### Step 4: Open a pull request

1. Create a branch in your fork, for example `i18n/<lang>`.
2. Make sure that the header of each file has `status: draft`.
3. Commit the files of `docs/<lang>/`.
4. Push the branch to your fork.
5. Open a pull request with the translation template. To use the template,
   add `?template=translation.md` to the URL of the pull request page:

   ```text
   https://github.com/amaklakov-droid/controlled-language-skill/compare/main...YOUR-USER:YOUR-BRANCH?expand=1&template=translation.md
   ```

   In the URL, replace `YOUR-USER` with your GitHub handle. Replace
   `YOUR-BRANCH` with the name of your branch.
6. Complete the checklist of the template.
7. Add the label `needs-native-review`.

The labeler workflow adds the labels `i18n` and `lang:<lang>` automatically.
If you cannot add labels, the maintainer adds `needs-native-review` for you.

### Step 5: Review the translation

A reviewer compares the translation with the English source on GitHub.

1. Open the pull request.
2. Click **Files changed**.
3. Open the English source of the file in a second browser tab.
4. Read the translation and compare it with the English source.
5. To propose a change, click the **+** button next to the line.
6. In the comment box, click the suggestion button. GitHub adds a
   `suggestion` block with the text of the line.
7. Write the correct text in the `suggestion` block. The translator can then
   apply the suggestion with one click.
8. When the translation is correct, click **Review changes**.
9. Select **Approve**.
10. Click **Submit review**.

Examine these items:

- The meaning is the same as in the English source.
- The text is natural and clear for a native speaker.
- The instructions use the standard imperative form of the language.
- The terms agree with the glossary.
- Code, commands, file names, links, and the header did not change.

The maintainer merges a translation only after at least one reviewer of the
language approves it. The reviewers are in [LANGUAGES.md](../LANGUAGES.md)
and in `.github/CODEOWNERS`.

### Step 6: Stamp the translation as reviewed

After the approval, the translator or the maintainer does these steps in the
branch of the pull request.

1. Examine the status of the files:

   ```bash
   python3 tools/i18n_status.py check
   ```

> **CAUTION:** Stamp only files that show `current`. If you stamp an
> outdated file, the tool shows it as current. But the file does not contain
> the latest English changes.

2. Set the status to `reviewed` and add the reviewer:

   ```bash
   python3 tools/i18n_status.py stamp docs/<lang>/*.md --status reviewed --reviewer @handle
   ```

3. Update the status table in [LANGUAGES.md](../LANGUAGES.md):

   ```bash
   python3 tools/i18n_status.py table
   ```

4. If this is the first publication of the language, add the language to the
   language bars. The language bar is the line of language links under the
   title of each page.
   - In `README.md` and in each `docs/*/README.md`, add a link to
     `docs/<lang>/README.md`.
   - In each page of `docs/en/`, add a link to the same page in
     `docs/<lang>/`.
5. Commit the changes.
6. Push the branch.

### Step 7: Merge and publish

The maintainer merges the pull request. The merge publishes the translation.
GitHub shows the new pages immediately. There is no other release step for
the documentation.

### Step 8: Keep the translation current

When an English source changes, its translations become outdated. The
workflow `.github/workflows/i18n-outdated.yml` finds them. It runs after each
push to `main` that changes `README.md` or a file in `docs/`.

- If a translation is outdated, missing, or untranslated, the workflow opens
  the issue "Translations are out of date". The issue has the label
  `translation-outdated` and a list of the files.
- If the issue is already open, the workflow updates the list.
- When all translations are current, the workflow closes the issue.

To update a translation:

1. Find the file in the issue "Translations are out of date".
2. Find the changes in the English source with
   `git log -p -- docs/en/<name>.md`. You can also use the history of the
   file on GitHub.
3. Change the translation to agree with the English source. An AI model can
   help. Give it the English changes and the current translation.
4. Stamp the file:

   ```bash
   python3 tools/i18n_status.py stamp docs/<lang>/<name>.md
   ```

   The command writes the new hash. If the status was `reviewed`, the command
   changes it to `draft`. No reviewer approved the new text yet.
5. Open a pull request with the translation template (step 4).
6. Get an approval from a reviewer of the language (step 5).
7. Stamp the file as reviewed (step 6).

If you change an English source, do not change translations in languages
that you do not speak. The workflow marks these translations as outdated. A
translator updates them later.

## Glossary

Each language can have a glossary: `docs/<lang>/glossary.md`. The glossary
gives the translation of each important term. It keeps the terms the same in
all files and for all translators.

The glossary is not a translation of an English file. Its header has
`source: none`. The tool does not count this file. To make the header, run
this command:

```bash
python3 tools/i18n_status.py stamp docs/<lang>/glossary.md --source none
```

Use a table with three columns:

```markdown
| English | Translation | Note |
| --- | --- | --- |
| skill | <translation> | <decision or reason> |
| checker script | <translation> | |
| level | <translation> | |
```

Follow these rules:

- Add a term when you translate it for the first time.
- Use the glossary in the AI prompt (`{GLOSSARY}`).
- If you change a term, change it in all files of the language in the same
  pull request.
- Write the reasons for your decisions in the "Note" column.

## What not to translate

Keep these items in English:

- The i18n header.
- Code blocks and inline code.
- Commands, options, and their values.
- File names, paths, and configuration keys, for example `non_english`.
- URLs and link targets. Change only the anchors of translated headings.
- Rule IDs, for example `S2` or `V3`.
- Names of products, projects, and standards: controlled-language,
  ASD-STE100, Simplified Technical English, Claude Code, GitHub.
- UI labels, when the product UI is in English.
- English example sentences that show the rules of controlled English. You
  can add a translation after an example.

Keep the meaning of the legal notices exactly. ASD-STE100 is a trademark of
ASD (Aerospace, Security and Defence Industries Association of Europe). This
project is not affiliated with ASD. Do not write that the project
or its output is compliant with ASD-STE100, certified, or endorsed by ASD.

## Disagreements between reviewers

Two reviewers can prefer different translations of a sentence or a term. Use
this procedure:

1. Discuss the options in the pull request. Give the reason for each option.
2. Select the option that most readers of the language understand. Prefer
   the standard form of the language to a regional form or a rare form.
3. If the reviewers do not agree, ask the maintainer to decide. Mention
   @amaklakov-droid in the pull request.
4. If the disagreement is about a term, write the decision in the glossary.

The decision of the maintainer is final. The maintainer can ask the language
maintainer for advice.

## Become a language maintainer

A language maintainer owns the folder of one language. GitHub asks the
language maintainer to review each pull request that changes this folder.
The language maintainer also keeps the glossary current.

To become a language maintainer:

1. Volunteer as a reviewer with the form
   [Volunteer as a native-speaker reviewer](https://github.com/amaklakov-droid/controlled-language-skill/issues/new?template=reviewer-signup.yml).
2. Review translation pull requests for the language.
3. After two or more reviews, ask the maintainer in an issue or in
   [Discussions](https://github.com/amaklakov-droid/controlled-language-skill/discussions).

The maintainer then does these steps:

1. Add your handle to the line of the language folder in
   `.github/CODEOWNERS`.
2. Add your handle to [LANGUAGES.md](../LANGUAGES.md) as the language
   maintainer.

## Language rules for the skill

The skill applies 32 universal rules to all languages. A **language file**
adds the rules for the grammar of one language. For example, the Russian
file removes verbal nouns and adverbial-participle clauses. The checker
script also reads the word table of the language file.

Language files are in `controlled-language/references/languages/`. The
name of the file is the language code: `ru.md`, `de.md`, `pt-BR.md`.

### Add a language file

1. Copy `controlled-language/references/languages/_template.md` to
   `<code>.md`.
2. Write the instruction form, the signal words, and the rules. Give each
   rule an ID: the language code in capital letters and a number (`DE1`).
   Connect each rule to a universal rule of `rules.md`.
3. Write the explanations in English. Write the examples in the language.
4. Add the word table. Write all forms of each word that the checker must
   find. Or write the start of the word and `*`.
5. Test the word table on a sample text:

   ```bash
   python3 controlled-language/scripts/check.py --lang <code> --level 2 sample.md
   ```

6. Set the status in the file to `draft`.
7. Open a pull request. Request a review from a native speaker.

You can make the first draft of the file with an AI model. Give the model
`_template.md`, `ru.md` (as an example), and `rules.md`. Then a native
speaker must examine each rule and each example.

### Review a language file

A native speaker of the language examines these items:

- Is the instruction form the usual form for technical documents?
- Are the signal words the usual words in this language?
- Is each rule correct for the grammar of the language?
- Are the "Not" examples bad, and are the "Use" examples good?
- Does each word in the word table have a better replacement? Does the
  word have other meanings that the checker must not flag?

After the approval, the reviewer changes the status in the file to
`reviewed` and adds their GitHub handle. Then the maintainer adds the file
to the table in `controlled-language/references/languages.md`.

## Tool reference

The tool `tools/i18n_status.py` needs Python 3.8 or later and no other
packages. Run it from the repository root.

| Command | Description |
| --- | --- |
| `check` | Shows the status of each translation. |
| `check --strict` | Also exits with code 1 if a file is invalid. |
| `check --github-summary` | Shows the status as Markdown for the summary of a GitHub Actions job. |
| `check --list-outdated` | Shows one line for each outdated, missing, or untranslated file. Tabs separate the fields: state, language code, translation, English source. |
| `stamp FILE...` | Writes or refreshes the header of each file. It sets `source_hash` to the hash of the current English source. |
| `table` | Regenerates the status table in [LANGUAGES.md](../LANGUAGES.md). |
| `new LANG` | Makes the folder `docs/LANG/`. It copies each English source to the folder and adds a header with `status: draft`. If the folder exists, the command stops. |

Options of the `stamp` command:

| Option | Description |
| --- | --- |
| `--status draft`, `--status reviewed` | Sets the status. Without this option, the command keeps the status. But if the English source changed, the command changes `reviewed` to `draft`. |
| `--reviewer @handle` | Adds a reviewer to `reviewed_by`. Repeat the option for more reviewers. |
| `--translated-with ai`, `--translated-with human` | Sets `translated_with`. The default for a new header is `ai`. |
| `--source PATH` | Sets the English source. Without this option, the command uses the header or the path of the file. Use `--source none` for a file that is not a translation. |

All commands accept `--root DIR`. The default is the parent folder of
`tools/`.
