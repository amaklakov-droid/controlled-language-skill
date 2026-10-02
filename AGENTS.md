# AGENTS.md

This repository contains **Controlled Language**, an open-source Agent Skill
(the [agentskills.io](https://agentskills.io) `SKILL.md` format). The skill
makes an AI agent write, rewrite, and review technical documentation in a
controlled language, in English or in other languages. The rules come from
the principles of ASD-STE100 Simplified Technical English (STE), at three
strictness levels. English gets the full rule set. Other languages get the
32 universal rules and the rules of their language file. The project
is not affiliated with ASD (Aerospace, Security and Defence Industries
Association of Europe).

## Where the skill is

```
controlled-language/
├── SKILL.md                    # entry point: workflow, levels, rules at a glance, output
├── references/
│   ├── rules.md                # rule catalog (39 rules) and the level matrix
│   ├── languages.md            # how the skill works with each language
│   ├── languages/              # language files (ru, de, fr, es) and _template.md
│   ├── word-choices.md         # English words to avoid; the checker parses this table
│   ├── configuration.md        # .controlled-language.yml, front matter, markers
│   └── examples.md             # calibration examples for each level
├── scripts/check.py            # checker (Python 3.8+, stdlib only)
└── assets/controlled-language.example.yml
```

The agent loads `SKILL.md` when the skill starts. It reads the files in
`references/` only when it needs them.

## How to install it

- Any agent: `npx skills add amaklakov-droid/controlled-language-skill`
- Claude Code plugin: `/plugin marketplace add amaklakov-droid/controlled-language-skill`,
  then `/plugin install controlled-language@controlled-language-skill`
- Manual: copy `controlled-language/` into the skills folder of the agent
  (`~/.claude/skills/`, `.agents/skills/`, `~/.codex/skills/`,
  `~/.copilot/skills/`, `~/.cursor/skills/`, `~/.gemini/skills/`).
- Chat models without skills: `prompts/system-prompt.md`.

Full instructions: [docs/en/installation.md](docs/en/installation.md).

## When to use this skill

Use the skill in these cases:

- The user wants clear, simple, or translation-friendly text in
  documentation, READMEs, procedures, help articles, release notes, UI text,
  or warnings, in any language.
- The user mentions ASD-STE100, STE, Simplified Technical English,
  controlled English, or "80% of the way to STE".
- The user asks for a review of documentation for readability.

## Rules for contributors (people and agents)

- Keep `controlled-language/SKILL.md` in English and shorter than about 500
  lines. Put details into `references/`.
- Never copy text from the ASD-STE100 standard or its dictionary. Write rules
  in your own words. ASD owns the copyright and the trademark.
- Never claim that output "complies with" or is "certified" for ASD-STE100.
- When you change the rule matrix in `references/rules.md`, update these
  files too:
  - the strength table in `scripts/check.py`;
  - the summary in `SKILL.md`;
  - `docs/en/levels.md`;
  - `prompts/system-prompt.md`.
- `references/word-choices.md` and the word tables of the language files
  are data sources of the checker. Keep their five columns.
- A new language file starts from `references/languages/_template.md` and
  has the status `draft` until a native speaker reviews it.
- Write English documentation at Level 2 of this skill. Check it with
  `python3 controlled-language/scripts/check.py --level 2 README.md docs/en`.
- English is the source language. When you change `README.md` or
  `docs/en/*.md`, do not edit translations unless you speak the language.
  `tools/i18n_status.py` marks them as outdated. See
  [docs/en/translating.md](docs/en/translating.md).
- Bump `version` in `.claude-plugin/plugin.json`,
  `.claude-plugin/marketplace.json`, and the `metadata.version` of
  `SKILL.md` together. Add an entry to `CHANGELOG.md`.
- Run the tests: `python3 -m unittest discover -s tests -v`.
- Validate the plugin: `claude plugin validate .`.
