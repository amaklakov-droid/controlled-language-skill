# Contributing

Thank you for your help. This page tells you how to contribute to
controlled-language. The project uses its own rules: write all English text in
controlled English at Level 2.

## Contents

- [Ways to contribute](#ways-to-contribute)
- [Pull request flow](#pull-request-flow)
- [Rules for documentation changes](#rules-for-documentation-changes)
- [Translations](#translations)
- [Rules for skill changes](#rules-for-skill-changes)
- [Legal notes](#legal-notes)
- [Code of conduct](#code-of-conduct)
- [Questions](#questions)

## Ways to contribute

- **Fix the documentation.** Correct errors and unclear text. Open a pull
  request with the change.
- **Translate the documentation.** Add a language, or review a translation
  in your native language. See
  [Translate the documentation](docs/en/translating.md).
- **Report skill output.** If the skill gives a bad result or a rule is
  wrong, open a
  [rule feedback issue](https://github.com/amaklakov-droid/controlled-language-skill/issues/new?template=rule-feedback.yml).
- **Improve the checker script.** Make
  `controlled-language/scripts/check.py` find more problems or fewer false
  problems. Add tests for each change.
- **Add examples.** Add before-and-after examples to `examples/`. Use text
  that you wrote yourself.
- **Report a bug.** If the installation or the checker script fails, open a
  [bug report](https://github.com/amaklakov-droid/controlled-language-skill/issues/new?template=bug-report.yml).

If you cannot open a pull request, use the form
[Suggest a documentation change](https://github.com/amaklakov-droid/controlled-language-skill/issues/new?template=docs-change.yml).

## Pull request flow

1. Fork the repository.
2. Create a branch, for example `fix/usage-typo`.
3. Make your change.
4. Run the tests:

   ```bash
   python3 -m unittest discover -s tests -v
   ```

5. If you changed English documentation, run the checker script at Level 2:

   ```bash
   python3 controlled-language/scripts/check.py --level 2 README.md docs/en
   ```

6. If you changed a translation, run the translation tool:

   ```bash
   python3 tools/i18n_status.py check
   ```

7. Commit the change.
8. Push the branch to your fork.
9. Open a pull request.
10. Complete the checklist in the pull request template.

Keep each pull request about one topic. A small pull request is faster to
review.

The labeler workflow adds labels from the changed files. The continuous integration (CI) workflow runs
the tests and the other checks in `.github/workflows/ci.yml`.

## Rules for documentation changes

English is the source language of the documentation. All translations come
from the English files.

- Write English documentation in controlled English at Level 2. Read the
  [rule catalog](controlled-language/references/rules.md) before you write.
- Use the same terms as the other pages of the documentation.
- If you do not speak the language of a translation, do not change the
  translation. The translation workflow marks it as outdated. A translator
  updates it later.
- If you speak the language, update the translation in the same pull
  request. Then stamp the file:

  ```bash
  python3 tools/i18n_status.py stamp docs/<lang>/<name>.md
  ```

- Do not edit the i18n header of a translation by hand. Use the `stamp`
  command.

## Translations

The translation process has these steps:

1. A person requests a language with an issue form.
2. The maintainer accepts the language and makes the language folder.
3. An AI model makes the draft translation.
4. The translator opens a pull request with the translation template.
5. Native speakers review the translation.
6. The translator stamps the files as reviewed.
7. The maintainer merges the pull request. The merge publishes the
   translation.
8. When the English source changes, the translation workflow opens an issue.
   A translator then updates the translation.

For all details, read [Translate the documentation](docs/en/translating.md).
For the status of each language, see [LANGUAGES.md](docs/LANGUAGES.md).

## Rules for skill changes

- Keep `controlled-language/SKILL.md` in English.
- Keep `SKILL.md` shorter than 500 lines. Put detailed information in
  `controlled-language/references/`.
- Write each rule in your own words.
- If you change the skill, increase the version in
  `.claude-plugin/plugin.json`, in `.claude-plugin/marketplace.json`, and in
  `metadata.version` of `controlled-language/SKILL.md`. Use the same version
  in the three files. Add an entry to `CHANGELOG.md`.
- Use semantic versioning:
  - Increase the patch number for a correction.
  - Increase the minor number for a new rule or a new option.
  - Increase the major number for a change that is not compatible with
    earlier versions.
- If you change the checker script, add tests in `tests/`.

## Legal notes

- **License.** The project uses the [Apache License 2.0](LICENSE). Each
  contribution that you submit is under the same license (section 5 of the
  license). You do not sign a contributor license agreement (CLA). You do not
  add a Developer Certificate of Origin (DCO) sign-off.
- **No text from the standard.** Do not copy text from the ASD-STE100
  standard or from its dictionary. This includes rule text, word lists, and
  examples. ASD (Aerospace, Security and Defence Industries Association of
  Europe) owns the copyright of the standard. Write rules and examples
  in your own words.
- **No claims of compliance.** Do not write that the project or its output
  is compliant with ASD-STE100 or certified. This project is not affiliated
  with ASD or endorsed by ASD.
- **Your right to share.** Submit only text and code that you have the right
  to share.

## Code of conduct

This project uses the Contributor Covenant as its code of conduct. Be
respectful to all people. To report a problem, read
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## Questions

- For questions about the skill, use
  [Discussions](https://github.com/amaklakov-droid/controlled-language-skill/discussions).
- For questions about the ASD-STE100 standard, go to
  [asd-ste100.org](https://www.asd-ste100.org/). This project is not
  affiliated with ASD and cannot answer for ASD.
