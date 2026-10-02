<!--
Thank you for your contribution. Complete this template.
For a translation, use the translation template: add ?template=translation.md to the URL of this page.
-->

## Description

<!-- What does this pull request change? Why? Link the issue, for example "Closes #12". -->

## Type of change

- [ ] Documentation (English)
- [ ] Translation
- [ ] Skill rules (`controlled-language/`)
- [ ] Checker script (`controlled-language/scripts/`)
- [ ] Infrastructure (`.github/`, `tools/`)

## Checklist

- [ ] The English text follows the rules of Level 2. I examined it with the checker script:
      `python3 controlled-language/scripts/check.py --level 2 README.md docs/en`
- [ ] If I changed `README.md` or a file in `docs/en/`, I updated the translations (for example `docs/ru/`) and stamped them. If I do not speak the language, I did not change the translation. The workflow marks it as outdated.
- [ ] If I changed the skill, I increased the version in `.claude-plugin/plugin.json` and in `.claude-plugin/marketplace.json`.
- [ ] The tests pass: `python3 -m unittest discover -s tests -v`
- [ ] I did not copy text from the ASD-STE100 standard or from its dictionary.
