# Changelog

All notable changes to this project are in this file. The project uses
[Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-10-02

### Changed

- Positioning: the skill is for any text that must be clear, easy to read,
  and unambiguous (documentation, instructions, explanations, emails,
  reports, answers), not only for technical documentation. The skill
  description, the README files, and the plugin manifests changed. The
  rules did not change.

### Added

- A banner for the README and a social preview image (`.github/assets/`).

## [1.0.0] - 2026-10-02

### Added

- The `controlled-language` skill: write, rewrite, review, and respond modes.
- Three levels: 1 Light, 2 Standard (default), 3 Strict, in all languages.
- Rule catalog with 39 rules and a strength matrix for each level: 32
  universal rules and 7 English-only rules.
- Language files with rules and word tables for Russian, German, French,
  and Spanish (drafts), and a template for new languages.
- Word list with replacements (`references/word-choices.md`).
- Project configuration file `.controlled-language.yml`: levels, path
  overrides, glossary of technical nouns and verbs, preferred terms.
- Front matter setting and inline markers.
- Checker script `scripts/check.py` (Python 3.8+, no dependencies) with
  automatic language detection and the word tables of the language files.
- One-file system prompt for chat models without skill support.
- Documentation in English and Russian.
- Language process: language requests, AI drafts, native review, and
  status tracking with `tools/i18n_status.py`, for the documentation and
  for the language files.
