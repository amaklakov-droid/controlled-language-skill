<!--
Translation pull request. Read docs/en/translating.md before you open it.
-->

## Language

- Language: <!-- for example Deutsch (German) -->
- Code (BCP 47): <!-- for example de -->

## Files

<!-- List the files that this pull request adds or changes, for example:
- docs/de/README.md
- docs/de/usage.md
-->

## How the draft was made

- [ ] AI model: <!-- name and version, for example Claude Sonnet -->
- [ ] By hand (`translated_with: human`)
- [ ] I reviewed the draft with the controlled-language skill at Level 2 (universal rules and the language file, if it exists).

## Checklist

- [ ] The i18n header of each file has `status: draft`. I made the headers with `python3 tools/i18n_status.py stamp`.
- [ ] I requested a review from a native-speaker reviewer of the language: <!-- @handle -->
- [ ] The label `needs-native-review` is on this pull request (or I asked the maintainer to add it).
- [ ] The terms agree with the glossary (`docs/<lang>/glossary.md`). I added new terms to the glossary.
- [ ] Links, anchors of headings that did not change, code blocks, commands, and file names are the same as in the English source.
- [ ] The text does not say that the project is compliant with ASD-STE100, certified, or endorsed by ASD.

## Output of the status tool

<!-- Run `python3 tools/i18n_status.py check` and paste the output for your language. -->

```text

```

<!--
After a native-speaker reviewer approves this pull request:
1. python3 tools/i18n_status.py stamp docs/<lang>/*.md --status reviewed --reviewer @handle
2. python3 tools/i18n_status.py table
3. For a new language, add the language to the language bars.
-->
