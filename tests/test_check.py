"""Tests for controlled-language/scripts/check.py.

Run from the repository root:

    python3 -m unittest discover -s tests -v
"""

import contextlib
import io
import json
import os
import re
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "controlled-language"
sys.path.insert(0, str(SKILL_DIR / "scripts"))

import check  # noqa: E402

try:
    import yaml  # type: ignore
except ImportError:  # pragma: no cover - depends on the environment
    yaml = None

WORDS = check.load_word_choices(check.DEFAULT_WORD_LIST)
EXAMPLE_CONFIG = SKILL_DIR / "assets" / "controlled-language.example.yml"
RULES_MD = SKILL_DIR / "references" / "rules.md"
LANGUAGES_DIR = SKILL_DIR / "references" / "languages"
RU_MD = LANGUAGES_DIR / "ru.md"
RU_SAMPLE = "В целях безопасности следует осуществить включение 2FA."


def run(text, level=2, config=None, lang="auto", suggestions=True, file_path=None):
    """Check a dedented text and return the report."""
    checker = check.Checker(WORDS, config)
    return checker.check_text(
        textwrap.dedent(text), path="test.md", file_path=file_path,
        level=level, lang=lang, suggestions=suggestions,
    )


def run_lang(text, level=2, lang="auto", languages_dir=LANGUAGES_DIR, config=None, suggestions=True):
    """Check a dedented text with a folder of language files."""
    checker = check.Checker(WORDS, config, Path(languages_dir) if languages_dir else None)
    return checker.check_text(
        textwrap.dedent(text), path="test.md", level=level, lang=lang, suggestions=suggestions,
    )


def word_table(*rows):
    """Make a language file with a word table in off/on markers."""
    lines = ["# Test", "", "## Word choices", "", "<!-- controlled-language: off -->",
             "| Avoid | Use instead | From level | Lint | Note |", "| --- | --- | --- | --- | --- |"]
    lines += list(rows) + ["<!-- controlled-language: on -->", ""]
    return "\n".join(lines)


def found(report, rule, severity=None):
    """Return the findings of one rule (and one severity)."""
    return [f for f in report.findings if f.rule == rule and (severity is None or f.severity == severity)]


def words(text, config=None):
    """Count the words of the whole text with the PU1 conventions."""
    checker = check.Checker(WORDS, config)
    prose = checker.cleaner.clean([(1, text)])
    return check.count_words(prose, 0, len(prose.text))


def sentences(text):
    prose = check.InlineCleaner().clean([(1, text)])
    return [prose.restore(a, b) for a, b in check.split_sentences(prose.text)]


def config_with(**values):
    return check.config_from_mapping(values)


class SentenceSplitTests(unittest.TestCase):
    def test_splits_on_end_punctuation_before_capital(self):
        self.assertEqual(sentences("Open the file. Close it! Is it closed? Yes."),
                         ["Open the file.", "Close it!", "Is it closed?", "Yes."])

    def test_keeps_decimals_and_versions(self):
        self.assertEqual(len(sentences("Install version 1.2.3 of the tool. It needs 2.5 GB of space.")), 2)

    def test_keeps_common_abbreviations(self):
        self.assertEqual(len(sentences("Use a tool, e.g. Git, for this. Then commit.")), 2)
        self.assertEqual(len(sentences("Compare Python vs. Go in the table.")), 1)
        self.assertEqual(len(sentences("See Fig. 2 and No. 5 for the layout.")), 1)

    def test_does_not_split_before_lowercase(self):
        self.assertEqual(len(sentences("The value is 5. then the tool stops.")), 1)

    def test_splits_after_closing_quote(self):
        self.assertEqual(sentences('He said "stop." Then he left.'), ['He said "stop."', "Then he left."])

    def test_placeholder_can_start_a_sentence(self):
        self.assertEqual(sentences("Run the command. `npm test` runs the tests."),
                         ["Run the command.", "`npm test` runs the tests."])

    def test_etc_can_end_a_sentence(self):
        self.assertEqual(len(sentences("Add files, folders, etc. Then save the project.")), 2)


class WordCountTests(unittest.TestCase):
    def test_number_with_unit_is_one_word(self):
        self.assertEqual(words("Wait 30 seconds."), 2)
        self.assertEqual(words("Use 5 MB or 10 % or 2 GB."), 6)

    def test_hyphenated_word_is_one_word(self):
        self.assertEqual(words("Use a read-only file."), 4)

    def test_code_paths_urls_are_one_word(self):
        text = "Run `npm install --save` in config.yaml from https://example.com/a/b or docs/a.md."
        self.assertEqual(words(text), 8)

    def test_glossary_term_and_ui_label_are_one_word(self):
        config = config_with(glossary={"technical_nouns": ["API key"]})
        self.assertEqual(words("Click **Save as Draft** to keep the API key.", config), 6)

    def test_list_intro_is_a_separate_sentence(self):
        report = run("""\
            Do these steps:

            1. Open the file.
            2. Close the file.
            """)
        self.assertEqual(report.sentences, 3)
        self.assertEqual(report.procedural, 3)


class MarkdownTests(unittest.TestCase):
    def test_code_blocks_are_skipped(self):
        report = run("""\
            Open the file.

            ```python
            utilize = "in order to"; x = 1
            ```

            ~~~
            Utilize this; it is being run.
            ~~~

                utilize the indented code
            """)
        self.assertEqual(report.findings, [])
        self.assertEqual(report.sentences, 1)

    def test_inline_code_urls_and_emails_are_not_checked(self):
        report = run("Do not `utilize` https://utilize.example.com or utilize@example.com today.")
        self.assertEqual(found(report, "W2"), [])

    def test_front_matter_is_skipped(self):
        report = run("""\
            ---
            title: Utilize the tool in order to start
            ---
            Open the file.
            """)
        self.assertEqual(report.findings, [])

    def test_html_comments_and_tags(self):
        report = run("""\
            <!-- utilize this in order to test -->
            <div align="center">
            Press <kbd>Ctrl</kbd> to utilize the menu.
            </div>
            """)
        self.assertEqual([(f.rule, f.line) for f in report.findings], [("W2", 3)])

    def test_off_and_on_markers(self):
        report = run("""\
            <!-- controlled-language: off -->
            Utilize the legal text; it stays.
            <!-- controlled-language: on -->
            Utilize the tool.
            """)
        self.assertEqual([(f.rule, f.line) for f in report.findings], [("W2", 4)])

    def test_level_marker_changes_level(self):
        report = run("""\
            The tool shows the running jobs.

            <!-- controlled-language: level 3 -->
            The tool shows the running jobs.
            """, level=None)
        self.assertEqual([(f.rule, f.severity, f.line) for f in found(report, "W6")],
                         [("W6", "suggestion", 1), ("W6", "violation", 4)])

    def test_cli_level_overrides_markers(self):
        report = run("""\
            <!-- controlled-language: level 3 -->
            The tool shows the running jobs.
            """, level=2)
        self.assertEqual([f.severity for f in found(report, "W6")], ["suggestion"])

    def test_markers_in_code_are_ignored(self):
        report = run("""\
            ```markdown
            <!-- controlled-language: off -->
            ```

            Write `<!-- controlled-language: off -->` before the text.

            Utilize the tool.
            """)
        self.assertEqual([f.rule for f in report.findings], ["W2"])

    def test_heading_gets_word_rules_only(self):
        long_heading = "## " + " ".join(["Word"] * 30)
        self.assertEqual(run(long_heading).findings, [])
        self.assertEqual(found(run("## Getting started", level=2), "W6", "suggestion")[0].line, 1)
        self.assertEqual(len(found(run("## Getting started", level=3), "W6", "violation")), 1)
        self.assertEqual(run("## Getting started").sentences, 0)

    def test_table_cells_get_word_rules_only(self):
        long_cell = " ".join(["word"] * 30)
        report = run(f"""\
            | Name | Description |
            | --- | --- |
            | a | {long_cell} |
            | b | Utilize the tool. |
            """)
        self.assertEqual([(f.rule, f.line) for f in report.findings], [("W2", 4)])
        self.assertEqual(report.sentences, 0)

    def test_short_table_cells_are_data_values(self):
        report = run("""\
            | Avoid | Use |
            | --- | --- |
            | set up | install |
            | utilize | use the tool in order to start |
            """)
        self.assertEqual([(f.rule, f.line) for f in report.findings], [("W2", 4)])

    def test_ordered_list_items_are_procedural(self):
        report = run("1. The file opens.\n2. The tool starts.\n")
        self.assertEqual((report.procedural, report.descriptive), (2, 0))
        report = run("- The file opens.\n- Open the file.\n")
        self.assertEqual((report.procedural, report.descriptive), (1, 1))

    def test_result_sentence_in_a_step_is_descriptive(self):
        report = run("3. Click **Connect**.\n   The status changes to **Online**.\n")
        self.assertEqual((report.procedural, report.descriptive), (1, 1))

    def test_line_numbers_are_kept(self):
        report = run("# Title\n\nThe first line of text\nand the second line of the text\nutilize the third line.\n")
        self.assertEqual([f.line for f in report.findings], [5])

    def test_links_and_images_keep_their_text(self):
        report = run("Read [how to utilize it](https://example.com).\n\n![Utilize the tool](a.png)\n")
        self.assertEqual(len(found(report, "W2")), 2)

    def test_link_text_that_is_a_file_name_is_not_checked(self):
        self.assertEqual(found(run("See also [NOTICE](NOTICE)."), "W9"), [])

    def test_run_in_heading_is_not_a_sentence(self):
        report = run("**Translations.** One is here. Two is here. Three is here. Four is here. Five is here. Six is here.\n")
        self.assertEqual(report.sentences, 6)
        self.assertEqual(found(report, "D2"), [])

    def test_quoted_short_mentions_are_not_checked(self):
        report = run('Do not use "should" or "may" in instructions.')
        self.assertEqual(found(report, "V5"), [])


class LevelTests(unittest.TestCase):
    def test_front_matter_short_form(self):
        report = run("---\ntitle: X\ncontrolled-language: 3\n---\nThe tool shows the running jobs.\n", level=None)
        self.assertEqual((report.level, report.level_source), (3, "front-matter"))
        self.assertEqual(found(report, "W6")[0].severity, "violation")

    def test_front_matter_long_form(self):
        report = run("---\ncontrolled-language:\n  level: 1\n---\nText.\n", level=None)
        self.assertEqual((report.level, report.level_source), (1, "front-matter"))

    def test_level_precedence(self):
        config = config_with(level=1, overrides=[{"path": "docs/safety/**", "level": 3}])
        self.assertEqual(check.resolve_level(2, 1, config, "docs/safety/a.md"), (2, "cli"))
        self.assertEqual(check.resolve_level(None, 1, config, "docs/safety/a.md"), (1, "front-matter"))
        self.assertEqual(check.resolve_level(None, None, config, "docs/safety/a/b.md"), (3, "override"))
        self.assertEqual(check.resolve_level(None, None, config, "docs/other.md"), (1, "config"))
        self.assertEqual(check.resolve_level(None, None, check.Config(), None), (2, "default"))

    def test_first_override_wins(self):
        config = config_with(overrides=[{"path": "docs/**", "level": 1}, {"path": "docs/safety/**", "level": 3}])
        self.assertEqual(check.resolve_level(None, None, config, "docs/safety/a.md"), (1, "override"))

    def test_override_uses_path_relative_to_config(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / check.CONFIG_NAME).write_text('overrides:\n  - path: "docs/safety/**"\n    level: 3\n')
            config = check.load_config(root / check.CONFIG_NAME)
            report = run("Text.", level=None, config=config, file_path=root / "docs" / "safety" / "a" / "b.md")
            self.assertEqual((report.level, report.level_source), (3, "override"))


class ConfigTests(unittest.TestCase):
    def test_subset_loader_reads_example_config(self):
        data = check.load_yaml_subset(EXAMPLE_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual(data["level"], 2)
        self.assertEqual(data["spelling"], "us")
        self.assertIn("docs/**/*.md", data["include"])
        self.assertEqual(data["overrides"][0], {"path": "docs/safety/**", "level": 3})
        self.assertIn({"use": "sign in", "not": ["log in", "login", "log on"]}, data["glossary"]["preferred_terms"])
        self.assertIn("API key", data["glossary"]["technical_nouns"])
        self.assertTrue(all(set(item) == {"word", "use"} for item in data["avoid_words"]))
        self.assertIn(data["non_english"], ("apply", "neutral"))
        config = check.config_from_mapping(data)
        self.assertEqual(config.overrides[0], ("docs/safety/**", 3))
        self.assertEqual(config.non_english, "apply")
        self.assertEqual(config.language, "auto")

    @unittest.skipIf(yaml is None, "PyYAML is not installed")
    def test_subset_loader_matches_pyyaml(self):
        text = EXAMPLE_CONFIG.read_text(encoding="utf-8")
        self.assertEqual(check.load_yaml_subset(text), yaml.safe_load(text))

    def test_subset_loader_features(self):
        text = textwrap.dedent("""\
            # A comment
            level: 3   # trailing comment
            name: "a # not a comment"
            single: 'it''s'
            flag: off
            empty:
            inline: [a, "b c", 'd, e', 4]
            nested:
              deep:
                key: value
            list:
            - one
            - two: 2
              three: x
            """)
        self.assertEqual(check.load_yaml_subset(text), {
            "level": 3, "name": "a # not a comment", "single": "it's", "flag": False,
            "empty": None, "inline": ["a", "b c", "d, e", 4],
            "nested": {"deep": {"key": "value"}},
            "list": ["one", {"two": 2, "three": "x"}],
        })

    def test_subset_loader_rejects_bad_indentation(self):
        with self.assertRaises(check.ConfigError):
            check.load_yaml_subset("level: 2\n   spelling: us\n")
        with self.assertRaises(check.ConfigError):
            check.load_yaml_subset("list: [a, b\n")

    def test_config_validation(self):
        with self.assertRaises(check.ConfigError):
            config_with(level=5)
        with self.assertRaises(check.ConfigError):
            config_with(spelling="fr")
        with self.assertRaises(check.ConfigError):
            config_with(overrides=[{"path": "a/**"}])
        self.assertEqual(config_with(non_english=False).non_english, "off")
        self.assertEqual(config_with(non_english="neutral").non_english, "apply")
        self.assertEqual(config_with().non_english, "apply")
        with self.assertRaises(check.ConfigError):
            config_with(non_english="ignore")

    def test_glob_matching(self):
        self.assertTrue(check.path_matches("docs/a/b/c.md", "docs/**/*.md"))
        self.assertTrue(check.path_matches("docs/c.md", "docs/**/*.md"))
        self.assertFalse(check.path_matches("blog/c.md", "docs/**/*.md"))
        self.assertTrue(check.path_matches("docs/legal/x/y.md", "docs/legal/**"))
        self.assertTrue(check.path_matches("sub/CHANGELOG.md", "CHANGELOG.md"))
        self.assertFalse(check.path_matches("sub/CHANGELOG.md", "/CHANGELOG.md"))
        self.assertTrue(check.path_matches("docs/a.md", "docs/"))


class CheckTests(unittest.TestCase):
    def test_s2_descriptive_limit(self):
        self.assertEqual(found(run(" ".join(["word"] * 25) + "."), "S2"), [])
        report = run(" ".join(["word"] * 26) + ".")
        self.assertEqual([(f.severity, f.line) for f in found(report, "S2")], [("violation", 1)])
        self.assertEqual(found(run(" ".join(["word"] * 30) + ".", level=1), "S2"), [])

    def test_s2_procedural_limit(self):
        self.assertEqual(found(run("Open " + " ".join(["file"] * 19) + "."), "S2"), [])
        report = run("Open " + " ".join(["file"] * 20) + ".")
        self.assertIn("max 20 in an instruction", found(report, "S2")[0].message)

    def test_d2_paragraph_length(self):
        six = " ".join(["The tool works."] * 6)
        self.assertEqual(found(run(six), "D2"), [])
        report = run(six + " The tool stops.")
        self.assertEqual(found(report, "D2")[0].severity, "violation")
        self.assertEqual(found(run(six + " The tool stops.", level=1), "D2"), [])
        self.assertEqual(report.paragraphs, 1)

    def test_s5_semicolon(self):
        text = "The tool starts; then it stops."
        self.assertEqual(found(run(text, level=1), "S5")[0].severity, "suggestion")
        self.assertEqual(found(run(text, level=2), "S5")[0].severity, "violation")
        self.assertEqual(found(run("The tool starts and stops."), "S5"), [])

    def test_s5_ignores_list_punctuation(self):
        self.assertEqual(found(run("- the first item;\n- the second item; and\n- the last item.\n"), "S5"), [])

    def test_v1_passive_in_instruction_is_violation(self):
        report = run("If the file is deleted, restart the service.")
        self.assertEqual([(f.rule, f.severity) for f in found(report, "V1")], [("V1", "violation")])

    def test_v1_passive_in_description(self):
        text = "The configuration file is read at startup."
        self.assertEqual(found(run(text, level=1), "V1")[0].severity, "suggestion")
        self.assertEqual(found(run(text, level=2), "V1")[0].severity, "warning")
        self.assertEqual(found(run("The token must be quickly renewed every day.", level=3), "V1")[0].severity, "warning")
        self.assertEqual(len(found(run("The token isn't renewed.", level=2), "V1")), 1)

    def test_v1_ignores_adjectives(self):
        for text in ("The price is based on usage.", "The tool is used to the load.",
                     "The file is closed.", "The service reads the file."):
            self.assertEqual(found(run(text), "V1"), [], text)

    def test_v2_perfect_and_continuous(self):
        text = "The migration has completed. The status is showing Done."
        self.assertEqual([f.severity for f in found(run(text, level=2), "V2")], ["suggestion", "suggestion"])
        self.assertEqual([f.severity for f in found(run(text, level=3), "V2")], ["violation", "violation"])
        self.assertEqual(found(run(text, level=1), "V2"), [])
        self.assertEqual(found(run("The status shows Done. The file is missing."), "V2"), [])

    def test_v3_phrasal_verbs(self):
        report = run("Set up the server, and then turned off the alarm.")
        findings = found(report, "V3")
        self.assertEqual([f.severity for f in findings], ["violation", "violation"])
        self.assertEqual(findings[0].suggestion, "install, configure, make")
        self.assertEqual(found(run("Set up the server.", level=1), "V3")[0].severity, "suggestion")
        self.assertEqual(found(run("Turn it off now."), "V3")[0].suggestion, "stop, disable")

    def test_v3_negative_cases(self):
        config = config_with(glossary={"technical_verbs": ["log in"]})
        for text, cfg in (("Make sure that the file exists.", None), ("Open the log in the folder.", None),
                          ("The set up is fast.", None), ("Log in to the dashboard.", config),
                          ("Put it in the list.", None)):
            self.assertEqual(found(run(text, config=cfg), "V3"), [], text)

    def test_w6_ing_words(self):
        text = "The tool shows the running jobs during the night."
        self.assertEqual(found(run(text, level=1), "W6"), [])
        self.assertEqual([f.severity for f in found(run(text, level=2), "W6")], ["suggestion"])
        self.assertEqual([f.severity for f in found(run(text, level=3), "W6")], ["violation"])
        self.assertEqual(found(run("Something is in the string settings.", level=3), "W6"), [])
        config = config_with(glossary={"technical_nouns": ["load balancing"]})
        self.assertEqual(found(run("Load balancing is fast.", level=3, config=config), "W6"), [])

    def test_word_choice_inflections(self):
        report = run("Utilize it. He utilizes it. She utilized it. We are utilizing it.", level=1)
        self.assertEqual([f.message for f in found(report, "W2")],
                         ['Avoid "Utilize"', 'Avoid "utilizes"', 'Avoid "utilized"', 'Avoid "utilizing"'])
        self.assertEqual(found(report, "W2")[0].suggestion, "use")

    def test_word_choice_levels(self):
        self.assertEqual(found(run("Begin the test.", level=1), "W2")[0].severity, "suggestion")
        self.assertEqual(found(run("Begin the test.", level=2), "W2")[0].severity, "violation")
        self.assertEqual(found(run("However, the test stops.", level=1), "W5"), [])
        self.assertEqual(found(run("However, the test stops.", level=2), "W5")[0].severity, "suggestion")
        self.assertEqual(found(run("However, the test stops.", level=3), "W5")[0].severity, "violation")

    def test_word_choice_rule_from_note(self):
        self.assertEqual([f.rule for f in run("Add files, folders, etc. to the list.").findings], ["W7"])
        self.assertEqual([f.rule for f in run("You should restart it.").findings], ["V5"])
        self.assertEqual([f.rule for f in run("Be careful with the file.").findings], ["SF3"])

    def test_word_choice_lint_no_is_skipped(self):
        report = run("Since the file is open, check it once while it runs.", level=3)
        self.assertEqual([f.rule for f in report.findings if f.rule in ("W1", "W2", "W5")], [])

    def test_word_choice_conditional_row_is_warning(self):
        self.assertEqual(found(run("Terminate the process.", level=1), "W2")[0].severity, "warning")
        self.assertEqual(found(run("Please open the file.", level=2), "W2")[0].severity, "warning")

    def test_project_avoid_words_and_preferred_terms(self):
        config = config_with(
            avoid_words=[{"word": "seamless", "use": "(delete the word)"}],
            glossary={"preferred_terms": [{"use": "sign in", "not": ["log in", "login"]}]},
        )
        report = run("Log in to the seamless dashboard. The login page opens. Sign in now.", level=1, config=config)
        self.assertEqual([(f.rule, f.severity, f.suggestion) for f in report.findings], [
            ("T1", "violation", "sign in"), ("W2", "violation", "(delete the word)"), ("T1", "violation", "sign in"),
        ])

    def test_w9_abbreviations(self):
        report = run("Use SSO for the portal. SSO is fast. The API and the JSON file are ready.")
        self.assertEqual([(f.rule, f.severity) for f in report.findings], [("W9", "warning")])
        defined = run("Single Sign-On (SSO) is fast. Use SSO for the portal.")
        self.assertEqual(found(defined, "W9"), [])
        reverse = run("SSO (Single Sign-On) is fast. Use SSO.")
        self.assertEqual(found(reverse, "W9"), [])
        self.assertEqual(found(run("Read rules W1 and PU1 in the CLI docs."), "W9"), [])

    def test_w8_spelling(self):
        report = run("Change the colour of the organised list.")
        self.assertEqual([(f.rule, f.suggestion) for f in report.findings], [("W8", "color"), ("W8", "organized")])
        uk = config_with(spelling="uk")
        self.assertEqual([f.suggestion for f in run("Change the color.", config=uk).findings], ["colour"])
        self.assertEqual([f.suggestion for f in run("Change the colour.", level=3, config=uk).findings], ["color"])
        self.assertEqual(run("Run the program. Read the analyses.", config=uk).findings, [])

    def test_p5_instruction_in_note(self):
        text = "Note: Restart the browser after the update."
        self.assertEqual(found(run(text, level=2), "P5")[0].severity, "warning")
        self.assertEqual(found(run(text, level=1), "P5")[0].severity, "suggestion")
        self.assertEqual(found(run("Note: The update does not change your settings."), "P5"), [])
        self.assertEqual(len(found(run("> [!NOTE]\n> Restart the browser.\n"), "P5")), 1)
        self.assertEqual(len(found(run("**Note:** If it fails, restart the browser."), "P5")), 1)

    def test_sf2_safety_text_in_note(self):
        report = run("NOTE: There is a risk of data loss.")
        self.assertEqual([(f.rule, f.severity) for f in report.findings], [("SF2", "warning")])

    def test_sf1_warning_starts_with_command(self):
        self.assertEqual(found(run("WARNING: Since the operation deletes all data, make a backup."), "SF1")[0].severity,
                         "warning")
        self.assertEqual(found(run("WARNING: Make a backup. The operation deletes all data."), "SF1"), [])
        self.assertEqual(found(run("> [!CAUTION]\n> Do not open the case.\n"), "SF1"), [])
        self.assertEqual(found(run("- **WARNING**: a risk to people."), "SF1"), [])

    def test_s6_double_negative(self):
        text = "It is not uncommon for the cache to be empty."
        self.assertEqual(found(run(text, level=1), "S6")[0].severity, "suggestion")
        self.assertEqual(found(run(text, level=2), "S6")[0].severity, "warning")
        self.assertEqual(found(run("It is not common."), "S6"), [])

    def test_rules_that_are_off_are_not_reported(self):
        report = run("The job has started and is running.", level=1)
        self.assertEqual(found(report, "W6") + found(report, "V2"), [])

    def test_no_suggestions(self):
        report = run("The tool shows the running jobs.", suggestions=False)
        self.assertEqual(report.findings, [])
        self.assertEqual(report.stats()["suggestions"], 0)


class NonEnglishTests(unittest.TestCase):
    LONG = " ".join(["слово"] * 27) + "."

    def test_other_language_uses_universal_rules_at_level_3(self):
        text = f"Используйте utilize; это running.\n\n{self.LONG}\n"
        report = run(text, level=3)
        self.assertEqual((report.language, report.level), ("ru", 3))  # No cap at Level 2.
        self.assertEqual(sorted({f.rule for f in report.findings}), ["S2", "S5"])
        self.assertEqual(found(report, "S2")[0].line, 3)
        self.assertEqual(found(report, "S5")[0].severity, "violation")

    def test_non_english_off_skips_the_file(self):
        report = run(self.LONG, config=config_with(non_english="off"))
        self.assertTrue(report.skipped)
        self.assertEqual(report.findings, [])

    def test_lang_option_forces_the_language(self):
        self.assertEqual(run("Utilize the tool.", lang="other").findings, [])
        self.assertEqual(run(self.LONG, lang="en").language, "en")


class LanguageDetectionTests(unittest.TestCase):
    def test_detects_latin_languages(self):
        samples = {
            "de": "Klicken Sie auf Speichern, um die Änderungen zu übernehmen. Die Datei wird dann gespeichert.",
            "fr": "Cliquez sur Enregistrer pour sauvegarder les modifications. Le fichier est ensuite fermé.",
            "es": "Haga clic en Guardar para guardar los cambios. El archivo se cierra después.",
            "pt": "Clique em Salvar para guardar as alterações. O arquivo não será fechado.",
            "it": "Fare clic su Salva per salvare le modifiche. Il file viene chiuso dopo il salvataggio.",
            "nl": "Klik op Opslaan om de wijzigingen te bewaren. Het bestand wordt daarna gesloten.",
            "pl": "Kliknij Zapisz, aby zapisać zmiany. Plik jest zamykany i nie można go edytować.",
        }
        for code, text in samples.items():
            self.assertEqual(check.detect_language_text(text), code, text)

    def test_english_stays_english(self):
        for text in (
            "Open the settings page and select the account. The tool saves the changes.",
            "Restart the service.",
            "The Russian word «следует» means \"should\". Do not use it in instructions.",
            "Die Hard is the name of the test. Use it for the load test of the server.",
            "`npm test` 1.2.3",
            "",
        ):
            self.assertEqual(check.detect_language_text(text), "en", text)

    def test_detects_cyrillic_variants(self):
        self.assertEqual(check.detect_language_text("Нажмите кнопку «Сохранить». Файл будет сохранён автоматически."), "ru")
        self.assertEqual(check.detect_language_text("Натисніть кнопку «Зберегти». Файл буде збережено автоматично."), "uk")
        self.assertEqual(check.detect_language_text("Націсніце кнопку «Захаваць». Файл будзе захаваны аўтаматычна."), "be")

    def test_detects_other_scripts(self):
        samples = {
            "el": "Πατήστε το κουμπί Αποθήκευση. Το αρχείο αποθηκεύεται αυτόματα.",
            "zh": "点击保存按钮。文件会自动保存。",
            "ja": "保存ボタンをクリックしてください。ファイルは自動的に保存されます。",
            "ko": "저장 버튼을 클릭하십시오. 파일이 자동으로 저장됩니다.",
            "ar": "انقر على زر الحفظ. يتم حفظ الملف تلقائيا.",
            "he": "לחץ על כפתור השמירה. הקובץ נשמר באופן אוטומטי.",
            "th": "คลิกปุ่มบันทึก ไฟล์จะถูกบันทึกโดยอัตโนมัติ",
            "other": "सहेजें बटन पर क्लिक करें। फ़ाइल अपने आप सहेजी जाती है।",
        }
        for code, text in samples.items():
            self.assertEqual(check.detect_language_text(text), code, text)

    def test_normalize_language(self):
        self.assertEqual(check.normalize_language("pt_br"), "pt-BR")
        self.assertEqual(check.normalize_language("RU"), "ru")
        self.assertEqual(check.normalize_language("zh-hant"), "zh-Hant")
        self.assertEqual(check.normalize_language("Auto"), "auto")
        self.assertEqual(check.normalize_language("other"), "other")
        for bad in ("русский", "e", "english language", "_template", "ru--RU"):
            self.assertIsNone(check.normalize_language(bad), bad)
        self.assertTrue(check.is_english("en-GB"))
        self.assertFalse(check.is_english("other"))


class LanguageSourceTests(unittest.TestCase):
    def test_front_matter_lang_overrides_auto(self):
        report = run_lang("---\nlang: ru\n---\nThe text is in English.\n")
        self.assertEqual((report.language, report.language_rules), ("ru", "ru.md"))
        report = run_lang("---\nlanguage: 'de'  # German\n---\nThe text is in English.\n", languages_dir=None)
        self.assertEqual(report.language, "de")

    def test_front_matter_nested_under_controlled_language(self):
        report = run_lang("---\ncontrolled-language:\n  level: 3\n  language: fr\n---\nText.\n", level=None)
        self.assertEqual((report.level, report.level_source, report.language), (3, "front-matter", "fr"))
        report = run_lang("---\ncontrolled-language: {level: 1, language: es}\n---\nText.\n", level=None)
        self.assertEqual((report.level, report.language), (1, "es"))
        self.assertEqual(check.front_matter_language(["lang: en", "controlled-language:", "  language: ru"]), "ru")
        self.assertIsNone(check.front_matter_language(["lang: auto", "title: X"]))

    def test_cli_lang_overrides_front_matter(self):
        report = run_lang("---\nlang: ru\n---\nUtilize the tool.\n", lang="en")
        self.assertEqual(report.language, "en")
        self.assertEqual([f.rule for f in report.findings], ["W2"])

    def test_config_language(self):
        config = config_with(language="de")
        self.assertEqual(run_lang("The text is in English.", config=config, languages_dir=None).language, "de")
        self.assertEqual(run_lang("---\nlang: ru\n---\nText.\n", config=config).language, "ru")
        self.assertEqual(run_lang("Text.", lang="en", config=config).language, "en")
        self.assertEqual(config_with(language="pt_br").language, "pt-BR")
        self.assertEqual(config_with(language=False).language, "no")  # YAML reads "no" as false.
        with self.assertRaises(check.ConfigError):
            config_with(language="Russian language")
        with self.assertRaises(check.UsageError):
            run_lang("Text.", lang="русский")


class RussianTests(unittest.TestCase):
    """The rules of the real references/languages/ru.md."""

    def test_russian_sample_at_level_2(self):
        report = run_lang(RU_SAMPLE, level=2)
        self.assertEqual((report.language, report.level, report.language_rules), ("ru", 2, "ru.md"))
        self.assertEqual([(f.rule, f.severity) for f in report.findings],
                         [("RU3", "violation"), ("RU8", "warning"), ("RU2", "violation")])
        self.assertEqual([f.message for f in report.findings],
                         ['Avoid "В целях"', 'Avoid "следует"', 'Avoid "осуществить"'])

    def test_russian_sample_at_level_1(self):
        report = run_lang(RU_SAMPLE, level=1)
        self.assertEqual([(f.rule, f.severity) for f in report.findings],
                         [("RU3", "violation"), ("RU8", "suggestion"), ("RU2", "suggestion")])
        self.assertEqual(run_lang(RU_SAMPLE, level=1, suggestions=False).findings[0].rule, "RU3")

    def test_prefix_entry_matches_word_starts(self):
        report = run_lang("Осуществление входа простое. Вход осуществляется автоматически. Это не неосуществимо.")
        self.assertEqual([f.message for f in found(report, "RU2")],
                         ['Avoid "Осуществление"', 'Avoid "осуществляется"'])

    def test_quoted_phrase_with_comma(self):
        report = run_lang("В связи с тем, что сервис занят, подождите. В связи с тем что сервис занят, "
                          "подождите. Я знаю, что сервис занят.")
        self.assertEqual([f.message for f in found(report, "RU3")],
                         ['Avoid "В связи с тем, что"', 'Avoid "В связи с тем что"'])
        self.assertEqual(found(report, "RU3")[0].suggestion, "потому что")

    def test_level_3_has_no_cap_and_uses_level_2_limits(self):
        text = "\n\n".join([
            " ".join(["слово"] * 25) + ".",
            " ".join(["слово"] * 26) + ".",
            "1. " + " ".join(["слово"] * 21) + ".",
            " ".join(["Слово идёт."] * 7),
        ])
        report = run_lang(text, level=3)
        self.assertEqual((report.language, report.level, report.level_source), ("ru", 3, "cli"))
        self.assertEqual([(f.line, f.message) for f in found(report, "S2")], [
            (3, "Sentence has 26 words (max 25 in a description at Level 3)"),
            (5, "Sentence has 21 words (max 20 in an instruction at Level 3)"),
        ])
        self.assertEqual([f.message for f in found(report, "D2")], ["Paragraph has 7 sentences (max 6 at Level 3)"])

    def test_level_1_uses_level_1_limits(self):
        report = run_lang(" ".join(["слово"] * 30) + "; " + "слово.", level=1)
        self.assertEqual([(f.rule, f.severity) for f in report.findings], [("S2", "violation"), ("S5", "suggestion")])
        self.assertIn("max 30 in a description at Level 1", found(report, "S2")[0].message)
        self.assertEqual(found(run_lang(" ".join(["слово"] * 30) + ".", level=1), "S2"), [])

    def test_english_only_checks_are_skipped(self):
        text = "Используйте utilize и SSO. Это running, colour и set up. Файл has been closed. Он is not uncommon."
        report = run_lang(text, level=3, lang="ru")
        self.assertEqual(report.findings, [])
        self.assertEqual(len(found(run_lang(text, level=3, lang="en"), "W2")), 1)

    def test_project_words_apply_to_other_languages(self):
        config = config_with(
            avoid_words=[{"word": "бесшовный", "use": "(delete the word)"}],
            glossary={"preferred_terms": [{"use": "вход", "not": ["логин"]}]},
        )
        report = run_lang("Откройте бесшовный экран. Введите логин.", level=1, config=config)
        self.assertEqual([(f.rule, f.severity, f.suggestion) for f in report.findings],
                         [("W2", "violation", "(delete the word)"), ("T1", "violation", "вход")])

    def test_localized_signal_words_sf2(self):
        report = run_lang("ПРИМЕЧАНИЕ: ВНИМАНИЕ, данные удалятся.")
        self.assertEqual([(f.rule, f.severity) for f in found(report, "SF2")], [("SF2", "warning")])
        self.assertEqual(len(found(run_lang("**Примечание:** Внимание! Файл удалится."), "SF2")), 1)
        self.assertEqual(len(found(run_lang("> [!NOTE]\n> ВНИМАНИЕ, файл удалится.\n"), "SF2")), 1)
        self.assertEqual(found(run_lang("ПРИМЕЧАНИЕ: Обратите внимание на поле."), "SF2"), [])
        self.assertEqual(found(run_lang("Обратите ВНИМАНИЕ на поле."), "SF2"), [])  # Not a note.

    def test_no_instruction_checks_for_other_languages(self):
        report = run_lang("ВНИМАНИЕ: Файл удалится, если вы закроете окно.\n\nПРИМЕЧАНИЕ: Перезапустите браузер.\n")
        self.assertEqual(found(report, "SF1") + found(report, "P5"), [])
        report = run_lang("NOTE: Restart the browser.\n\nЭто русский текст о настройке сервиса и о файлах.\n")
        self.assertEqual(report.language, "ru")
        self.assertEqual(len(found(report, "P5")), 1)  # An English note in the document.

    def test_real_ru_md_parses(self):
        rules = check.LanguageRules.load("ru", RU_MD)
        by_phrase = {phrase: row for row in rules.word_choices for phrase in row.phrases}
        self.assertIs(by_phrase["в связи с тем, что"], by_phrase["в связи с тем что"])
        self.assertEqual(by_phrase["осуществ*"].rule, "RU2")
        self.assertEqual(by_phrase["в целях"].from_level, 1)
        self.assertEqual(by_phrase["и т.п."].rule, "W7")
        self.assertFalse(by_phrase["следует"].inflect)
        self.assertEqual(rules.strengths["RU2"], ("prefer", "must", "must"))
        self.assertEqual(rules.strengths["RU6"][0], "-")
        self.assertEqual(rules.signal_words["note"], ["ПРИМЕЧАНИЕ"])

    def test_all_language_files_parse(self):
        files = [path for path in LANGUAGES_DIR.glob("*.md") if not path.name.startswith("_")]
        self.assertIn(RU_MD, files)
        for path in files:  # A file can have no word table, but a table must be correct.
            rules = check.LanguageRules.load(path.stem, path)
            self.assertIsInstance(rules.word_choices, list, path.name)


class LanguageFileTests(unittest.TestCase):
    """Language files in a temporary folder."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)

    def tearDown(self):
        self.folder.cleanup()

    def write(self, name, text):
        (self.root / name).write_text(text, encoding="utf-8")

    def test_language_without_file_gets_universal_rules_only(self):
        report = run_lang("Klicken Sie auf Speichern; die Durchführung erfolgt dann.", lang="de", languages_dir=self.root)
        self.assertEqual((report.language, report.language_rules), ("de", None))
        self.assertEqual([f.rule for f in report.findings], ["S5"])
        self.assertEqual(report.language_label(), "de (universal rules only: no language file)")

    def test_primary_subtag_fallback(self):
        self.write("pt.md", word_table("| efetuar, efetue | fazer | 1 | yes | Rule PT2. |"))
        self.write("_template.md", word_table("| fazer | x | 1 | yes | |"))
        report = run_lang("Efetue o login.", lang="pt-BR", languages_dir=self.root)
        self.assertEqual((report.language, report.language_rules), ("pt-BR", "pt.md"))
        self.assertEqual([(f.rule, f.severity) for f in report.findings], [("PT2", "violation")])
        self.assertEqual(report.language_label(), "pt-BR (language rules: pt.md)")
        self.assertIsNone(check.find_language_file("_template", self.root))

    def test_table_format(self):
        rows = check.parse_word_choices(word_table(
            '| "a, b", c*, `d` | x | 3 | yes | |',
            "| e | y | 2 | no | Rule SF3. Keep it. |",
            "| f | z | 1 | yes | Rule XYZ12. |",
        ), english=False)
        self.assertEqual([(r.phrases, r.rule, r.inflect) for r in rows], [
            (["a, b", "c*", "d"], "W2", False), (["e"], "SF3", False), (["f"], "XYZ12", False),
        ])
        self.assertTrue(rows[1].conditional)
        self.assertEqual(check.parse_word_choices("# No table\n", english=False, required=False), [])
        with self.assertRaises(check.WordListError):
            check.parse_word_choices(word_table("| a | b | 2 | yes | Rule XYZ12. |"))  # Unknown rule in English.

    def test_comma_is_optional_in_both_directions(self):
        with_comma = re.compile(check.phrase_regex(["в связи с тем, что"], inflect=False), re.I)
        without_comma = re.compile(check.phrase_regex(["in case if"]), re.I)
        self.assertTrue(with_comma.search("В связи с тем что"))
        self.assertTrue(with_comma.search("в связи  с тем,что"))
        self.assertFalse(with_comma.search("в связи с этим, что"))
        self.assertTrue(without_comma.search("In case, if it fails"))

    def test_no_english_inflections_in_language_tables(self):
        self.assertFalse(re.search(check.phrase_regex(["utilize"], inflect=False), "utilized"))
        self.assertTrue(re.search(check.phrase_regex(["utilize"]), "utilized"))
        self.write("de.md", word_table("| test | Prüfung | 1 | yes | Rule DE3. |"))
        report = run_lang("Der test läuft. Die tests laufen.", lang="de", languages_dir=self.root)
        self.assertEqual([f.message for f in report.findings], ['Avoid "test"'])

    def test_unicode_case_insensitive_matching(self):
        self.write("el.md", word_table("| παρακαλώ | (delete the word) | 1 | yes | Rule EL3. |"))
        self.write("fr.md", word_table("| procéder à, effectu* | (use the action verb) | 1 | yes | Rule FR2. |"))
        self.assertEqual([f.rule for f in run_lang("Παρακαλώ πατήστε το κουμπί.", languages_dir=self.root).findings],
                         ["EL3"])
        report = run_lang("Procéder à la mise à jour. Le système effectue la copie.", lang="fr", languages_dir=self.root)
        self.assertEqual([f.message for f in report.findings], ['Avoid "Procéder à"', 'Avoid "effectue"'])

    def test_cjk_sentence_length_is_not_checked(self):
        long_sentence = "这是一个很长的句子" * 20 + "。"
        report = run_lang(long_sentence + "\n\n" + "文件已保存。" * 7 + "\n", languages_dir=self.root)
        self.assertEqual(report.language, "zh")
        self.assertEqual([f.rule for f in report.findings], ["D2"])
        self.assertIn("S2 not checked", report.language_label())

    def test_non_english_apply_and_off(self):
        for value in ("neutral", "apply"):
            report = run_lang(RU_SAMPLE, config=config_with(non_english=value))
            self.assertFalse(report.skipped, value)
            self.assertEqual(len(report.findings), 3)
        off = config_with(non_english="off")
        report = run_lang(RU_SAMPLE, config=off)
        self.assertTrue(report.skipped)
        self.assertEqual((report.findings, report.language_rules), ([], "ru.md"))
        self.assertFalse(run_lang("Utilize the tool.", config=off).skipped)

    def test_severity_for_other_languages(self):
        self.assertIsNone(check.severity_for("W6", 3, "ru"))
        self.assertEqual(check.severity_for("W6", 3, "en"), "violation")
        self.assertEqual(check.severity_for("S5", 1, "ru"), "suggestion")
        self.assertEqual(check.severity_for("S5", 3, "ru"), "violation")
        self.assertEqual(check.severity_for("SF2", 3, "other", reliable=False), "warning")


class EnglishRegressionTests(unittest.TestCase):
    SAMPLE = """\
        # Getting started

        Utilize the tool in order to set up the server. The job is being run; it has completed.

        NOTE: Restart the browser. There is a risk of data loss.

        WARNING: Since the operation deletes all data, make a backup.

        Use SSO for the portal. Change the colour of the list, e.g. red.
        """

    def test_english_sample_is_unchanged(self):
        report = run_lang(self.SAMPLE, level=2)
        self.assertEqual((report.language, report.language_rules, report.language_label()), ("en", None, "en"))
        self.assertEqual([(f.line, f.rule, f.severity) for f in report.findings], [
            (1, "W6", "suggestion"), (3, "W2", "violation"), (3, "W2", "violation"), (3, "V3", "violation"),
            (3, "S5", "violation"), (3, "V1", "warning"), (3, "V2", "suggestion"), (5, "P5", "warning"),
            (5, "SF2", "warning"), (7, "SF1", "warning"), (9, "W9", "warning"), (9, "W2", "violation"),
            (9, "W8", "violation"),
        ])


class WordListTests(unittest.TestCase):
    def test_parses_the_real_word_list(self):
        self.assertGreater(len(WORDS), 40)
        by_phrase = {phrase: row for row in WORDS for phrase in row.phrases}
        self.assertIs(by_phrase["etc."], by_phrase["and so on"])
        self.assertEqual(by_phrase["etc."].rule, "W7")
        self.assertEqual(by_phrase["should"].rule, "V5")
        self.assertEqual(by_phrase["however"].rule, "W5")
        self.assertEqual(by_phrase["utilize"].rule, "W2")
        self.assertFalse(by_phrase["since"].lint)
        self.assertTrue(by_phrase["leverage"].verb_only)

    def test_custom_table_and_errors(self):
        text = "| Avoid | Use instead | From level | Lint | Note |\n| --- | --- | --- | --- | --- |\n" \
               "| foo, bar baz | qux | 2 | yes | Rule V5. |\n| zap | zip | 3 | no | |\n"
        rows = check.parse_word_choices(text)
        self.assertEqual([(r.phrases, r.rule, r.lint) for r in rows],
                         [(["foo", "bar baz"], "V5", True), (["zap"], "W5", False)])
        with self.assertRaises(check.WordListError):
            check.parse_word_choices("| A | B |\n| --- | --- |\n")
        with self.assertRaises(check.WordListError):
            check.parse_word_choices(text.replace("| 2 |", "| 9 |"))

    def test_inflections(self):
        self.assertTrue({"utilize", "utilizes", "utilized", "utilizing"} <= check.inflections("utilize"))
        self.assertTrue({"modifies", "modified", "modifying"} <= check.inflections("modify"))
        self.assertTrue({"permits", "permitted", "permitting"} <= check.inflections("permit"))


class SyncTests(unittest.TestCase):
    """The tables in the code must match rules.md."""

    @staticmethod
    def _table_after(heading):
        lines = RULES_MD.read_text(encoding="utf-8").splitlines()
        start = next(i for i, line in enumerate(lines) if line.strip() == heading)
        rows = []
        for line in lines[start + 1:]:
            if line.startswith("#"):
                break
            if line.strip().startswith("|") and not check.is_table_separator(line):
                rows.append(check.split_table_row(line))
            elif rows and not line.strip().startswith("|"):
                break
        return rows[1:]

    def test_rule_matrix_matches_rules_md(self):
        def normalize(cell):
            cell = re.sub(r"\s*\(.*?\)", "", cell.strip().lower())
            return {"—": "-", "must / prefer": "must/prefer"}.get(cell, cell)

        matrix = {row[0]: tuple(normalize(cell) for cell in row[2:6]) for row in self._table_after("## Rule matrix")}
        self.assertEqual(matrix, check.RULE_MATRIX)

    def test_phrasal_suggestions_match_rules_md(self):
        rows = self._table_after("### V3 — No phrasal verbs")
        self.assertTrue(rows)
        for avoid, use in rows:
            self.assertEqual(check.PHRASAL_SUGGESTIONS.get(avoid), use, avoid)


class CliTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.old_cwd = os.getcwd()
        os.chdir(self.folder.name)

    def tearDown(self):
        os.chdir(self.old_cwd)
        self.folder.cleanup()

    def cli(self, *args, stdin=None):
        out, err = io.StringIO(), io.StringIO()
        old_stdin = sys.stdin
        if stdin is not None:
            sys.stdin = io.TextIOWrapper(io.BytesIO(stdin.encode("utf-8")), encoding="utf-8")
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                try:
                    code = check.main(list(args))
                except SystemExit as error:
                    code = error.code
        finally:
            sys.stdin = old_stdin
        return code, out.getvalue(), err.getvalue()

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text), encoding="utf-8")
        return path

    def test_json_shape(self):
        self.write("a.md", "Utilize the tool.\n")
        code, out, _ = self.cli("--format", "json", "a.md")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["version"], "1.0")
        file = data["files"][0]
        self.assertEqual(set(file), {
            "path", "level", "level_source", "language", "language_rules", "skipped", "stats", "findings",
        })
        self.assertIsNone(file["language_rules"])
        self.assertEqual(set(file["stats"]), {
            "sentences", "procedural", "descriptive", "paragraphs", "violations", "warnings",
            "suggestions", "violations_per_100_sentences",
        })
        self.assertEqual(set(file["findings"][0]), {"line", "rule", "severity", "message", "excerpt", "suggestion"})
        self.assertEqual(file["stats"]["violations_per_100_sentences"], 100.0)
        self.assertIn("N1", data["summary"]["not_checked"])
        self.assertNotIn("S2", data["summary"]["not_checked"])
        self.assertEqual(data["summary"]["violations"], 1)

    def test_text_output(self):
        self.write("a.md", "Utilize the tool.\n")
        code, out, _ = self.cli("a.md")
        lines = out.splitlines()
        self.assertEqual(lines[0], 'a.md:1: violation W2 Avoid "Utilize" — "Utilize the tool." → use')
        self.assertTrue(lines[1].startswith("a.md: Level 2 (default), en, 1 sentence (1 procedural, 0 descriptive)"))
        self.assertTrue(lines[-1].startswith("Total: 1 file, 1 sentence: 1 violation"))
        self.assertNotIn("\033[", out)

    def test_exit_codes(self):
        self.write("bad.md", "Utilize the tool.\n")
        self.write("warn.md", "Use SSO for the portal.\n")
        self.assertEqual(self.cli("bad.md")[0], 0)
        self.assertEqual(self.cli("--fail-on", "violation", "bad.md")[0], 1)
        self.assertEqual(self.cli("--fail-on", "violation", "warn.md")[0], 0)
        self.assertEqual(self.cli("--fail-on", "warning", "warn.md")[0], 1)
        self.assertEqual(self.cli("missing.md")[0], 2)
        self.assertEqual(self.cli("--level", "4", "bad.md")[0], 2)
        self.write("broken.yml", "level: 7\n")
        self.assertEqual(self.cli("--config", "broken.yml", "bad.md")[0], 2)
        self.assertEqual(self.cli("--word-list", "missing.md", "bad.md")[0], 2)

    def test_stdin(self):
        code, out, _ = self.cli("--format", "json", "--level", "3", "-", stdin="The tool shows the running jobs.\n")
        data = json.loads(out)
        self.assertEqual(data["files"][0]["path"], "<stdin>")
        self.assertEqual(data["files"][0]["level_source"], "cli")
        self.assertEqual(data["files"][0]["findings"][0]["rule"], "W6")

    def test_config_discovery_and_include_exclude(self):
        self.write(check.CONFIG_NAME, """\
            level: 3
            include:
              - "docs/**/*.md"
            exclude:
              - "docs/legal/**"
            overrides:
              - path: "docs/blog/**"
                level: 1
            """)
        self.write("docs/a.md", "Text.\n")
        self.write("docs/blog/b.md", "Text.\n")
        self.write("docs/legal/c.md", "Text.\n")
        self.write("docs/d.txt", "Text.\n")
        self.write("notes.md", "Text.\n")
        sub = self.root / "docs" / "blog"
        os.chdir(sub)  # The script finds the config in a parent folder.
        code, out, _ = self.cli("--format", "json", str(self.root))
        files = {Path(f["path"]).relative_to(self.root).as_posix(): (f["level"], f["level_source"])
                 for f in json.loads(out)["files"]}
        self.assertEqual(files, {"docs/a.md": (3, "config"), "docs/blog/b.md": (1, "override")})

    def test_help_lists_unchecked_rules(self):
        code, out, _ = self.cli("--help")
        self.assertEqual(code, 0)
        self.assertIn("not check these rules", out)
        self.assertIn("N1", out)

    def test_help_documents_languages(self):
        code, out, _ = self.cli("--help")
        for text in ("--lang CODE", "pt-BR", "--languages-dir", "lang: ru", "language: ru", "<code>.md"):
            self.assertIn(text, out)
        self.assertNotIn("Level 2 for", out)

    def test_language_report_in_text_and_json(self):
        languages = self.root / "languages"
        languages.mkdir()
        (languages / "ru.md").write_text(RU_MD.read_text(encoding="utf-8"), encoding="utf-8")
        self.write("ru.md", RU_SAMPLE + "\n")
        self.write("de.md", "Klicken Sie auf Speichern, um die Änderungen zu übernehmen.\n")
        code, out, _ = self.cli("--languages-dir", "languages", "--level", "3", "ru.md", "de.md")
        self.assertIn("ru.md: Level 3 (cli), ru (language rules: ru.md), 1 sentence", out)
        self.assertIn("de.md: Level 3 (cli), de (universal rules only: no language file), 1 sentence", out)
        self.assertIn("ru.md:1: violation RU2 Avoid \"осуществить\"", out)
        self.assertNotIn("cap", out.lower())
        code, out, _ = self.cli("--languages-dir", "languages", "--format", "json", "ru.md", "de.md")
        files = {f["path"]: (f["language"], f["language_rules"], f["level"]) for f in json.loads(out)["files"]}
        self.assertEqual(files, {"ru.md": ("ru", "ru.md", 2), "de.md": ("de", None, 2)})

    def test_lang_option(self):
        self.write("a.md", "Utilize the tool.\n")
        code, out, _ = self.cli("--format", "json", "--lang", "RU", "a.md")
        self.assertEqual(json.loads(out)["files"][0]["language"], "ru")
        self.assertEqual(json.loads(out)["files"][0]["findings"], [])
        code, out, _ = self.cli("--format", "json", "--lang", "other", "a.md")
        self.assertEqual(json.loads(out)["files"][0]["language_rules"], None)
        self.assertEqual(self.cli("--lang", "русский", "a.md")[0], 2)
        self.assertEqual(self.cli("--languages-dir", "missing", "a.md")[0], 2)

    def test_config_language_and_skip(self):
        self.write(check.CONFIG_NAME, "language: ru\nnon_english: off\n")
        self.write("a.md", "Utilize the tool.\n")
        code, out, _ = self.cli("a.md")
        self.assertIn("a.md: skipped (ru: the text is not in English, and non_english is off)", out)
        self.assertIn("(1 skipped)", out)


if __name__ == "__main__":
    unittest.main()
