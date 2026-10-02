"""Tests for tools/i18n_status.py.

Run from the repository root:

    python3 -m unittest discover -s tests -v
"""

import contextlib
import hashlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import i18n_status as i18n  # noqa: E402


README = "# Project\n\n**English** · [Русский](docs/ru/README.md)\n\nRead [usage](docs/en/usage.md) and [license](LICENSE).\n"
USAGE = "# Usage\n\nRun the tool.\n"
LEVELS = "# Levels\n\nThe skill has three levels.\n"
LANGUAGES = "# Languages\n\nIntro text.\n\n<!-- i18n-table:start -->\nold table\n<!-- i18n-table:end -->\n\nFooter text.\n"


class RepoTestCase(unittest.TestCase):
    """A temporary repository with three English sources."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.write("README.md", README)
        self.write("docs/en/usage.md", USAGE)
        self.write("docs/en/levels.md", LEVELS)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(str(path), "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        return path

    def read(self, rel):
        with open(str(self.root / rel), encoding="utf-8", newline="") as handle:
            return handle.read()

    def translate(self, rel, source, status="draft", source_hash=None, body="# Перевод\n\nТекст.\n", reviewers=()):
        header = i18n.Header(
            source=source,
            source_hash=source_hash or i18n.source_hash(self.root / source),
            status=status,
            translated_with="ai",
            reviewed_by=list(reviewers),
        )
        return self.write(rel, header.render() + "\n" + body)

    def entries(self, lang="ru"):
        report = i18n.collect(self.root)
        for language in report.languages:
            if language.code == lang:
                return {entry.path: entry for entry in language.entries}
        return {}

    def run_cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = i18n.main(["--root", str(self.root)] + list(args))
        return code, out.getvalue(), err.getvalue()


class HashTests(unittest.TestCase):
    def test_hash_is_first_12_hex_chars_of_sha256(self):
        data = b"# Title\n\nText.\n"
        self.assertEqual(i18n.hash_bytes(data), hashlib.sha256(data).hexdigest()[:12])
        self.assertRegex(i18n.hash_bytes(data), r"^[0-9a-f]{12}$")

    def test_hash_ignores_line_endings(self):
        lf = i18n.hash_bytes(b"a\nb\n")
        self.assertEqual(lf, i18n.hash_bytes(b"a\r\nb\r\n"))
        self.assertEqual(lf, i18n.hash_bytes(b"a\rb\r"))

    def test_hash_changes_with_content(self):
        self.assertNotEqual(i18n.hash_bytes(b"a\n"), i18n.hash_bytes(b"b\n"))


class HeaderTests(unittest.TestCase):
    def test_render_and_parse_roundtrip(self):
        header = i18n.Header("docs/en/usage.md", "1a2b3c4d5e6f", "reviewed", "human", ["@alice", "@bob-2"])
        parsed = i18n.parse_text(header.render() + "\n# Body\n")
        self.assertEqual(parsed.errors, [])
        self.assertEqual(parsed.header, header)

    def test_render_matches_documented_format(self):
        header = i18n.Header("docs/en/usage.md", "1a2b3c4d5e6f", "draft", "ai", [])
        self.assertEqual(
            header.render(),
            "<!--\ni18n:\n  source: docs/en/usage.md\n  source_hash: 1a2b3c4d5e6f\n"
            "  status: draft\n  translated_with: ai\n  reviewed_by: []\n-->\n",
        )

    def test_reviewers_with_and_without_at_sign_and_quotes(self):
        text = (
            "<!--\ni18n:\n  source: docs/en/a.md\n  source_hash: 1a2b3c4d5e6f\n  status: reviewed\n"
            "  translated_with: ai\n  reviewed_by: [@alice, bob, \"@carol\"]\n-->\n"
        )
        self.assertEqual(i18n.parse_text(text).header.reviewed_by, ["@alice", "@bob", "@carol"])

    def test_block_list_of_reviewers(self):
        text = (
            "<!--\ni18n:\n  source: docs/en/a.md\n  source_hash: 1a2b3c4d5e6f\n  status: reviewed\n"
            "  translated_with: human\n  reviewed_by:\n    - @alice\n    - @bob\n-->\n"
        )
        self.assertEqual(i18n.parse_text(text).header.reviewed_by, ["@alice", "@bob"])

    def test_no_header(self):
        parsed = i18n.parse_text("# Title\n\n<!--\ni18n:\n-->\n")
        self.assertIsNone(parsed.block)
        self.assertIsNone(parsed.header)

    def test_bad_values_are_errors(self):
        text = (
            "<!--\ni18n:\n  source: docs/en/a.md\n  source_hash: XYZ\n  status: done\n"
            "  translated_with: robot\n  reviewed_by: [not a handle]\n-->\n"
        )
        parsed = i18n.parse_text(text)
        self.assertIsNone(parsed.header)
        joined = " ".join(parsed.errors)
        for word in ("source_hash", "status", "translated_with", "reviewed_by"):
            self.assertIn(word, joined)

    def test_missing_fields_are_errors(self):
        parsed = i18n.parse_text("<!--\ni18n:\n  status: draft\n-->\n")
        self.assertIsNone(parsed.header)
        self.assertTrue(any("source" in error for error in parsed.errors))

    def test_unclosed_comment_is_error(self):
        parsed = i18n.parse_text("<!--\ni18n:\n  source: docs/en/a.md\n# Title\n")
        self.assertIsNotNone(parsed.block)
        self.assertIsNone(parsed.header)

    def test_header_after_front_matter(self):
        header = i18n.Header("docs/en/a.md", "1a2b3c4d5e6f", "draft", "ai", [])
        parsed = i18n.parse_text("---\ntitle: A\n---\n" + header.render() + "# A\n")
        self.assertEqual(parsed.header, header)

    def test_source_none_needs_no_hash(self):
        parsed = i18n.parse_text("<!--\ni18n:\n  source: none\n  status: draft\n  reviewed_by: []\n-->\n")
        self.assertEqual(parsed.errors, [])
        self.assertTrue(parsed.header.standalone)

    def test_with_header_inserts_after_front_matter_and_keeps_body(self):
        header = i18n.Header("docs/en/a.md", "1a2b3c4d5e6f", "draft", "ai", [])
        lines = "---\ntitle: A\n---\n# A\n\nBody.\n".splitlines(keepends=True)
        text = i18n.with_header(lines, None, header, "\n")
        self.assertTrue(text.startswith("---\ntitle: A\n---\n<!--\n"))
        self.assertTrue(text.endswith("-->\n\n# A\n\nBody.\n"))


class LanguageNameTests(unittest.TestCase):
    def test_known_and_unknown_codes(self):
        self.assertEqual(i18n.language_name("ru"), "Русский")
        self.assertEqual(i18n.language_name("de"), "Deutsch")
        self.assertEqual(i18n.language_name("pt-BR"), "Português (Brasil)")
        self.assertEqual(i18n.language_name("es-MX"), "Español (es-MX)")
        self.assertEqual(i18n.language_name("xx"), "xx")
        self.assertEqual(i18n.language_label("ru"), "Русский (Russian)")

    def test_language_codes(self):
        for code in ("ru", "pt-BR", "zh-Hans", "fil"):
            self.assertTrue(i18n.is_language_code(code), code)
        for code in ("RU", "russian", "r", "img_1", ""):
            self.assertFalse(i18n.is_language_code(code), code)

    def test_path_mapping(self):
        self.assertEqual(i18n.translation_path("README.md", "ru"), "docs/ru/README.md")
        self.assertEqual(i18n.translation_path("docs/en/usage.md", "ru"), "docs/ru/usage.md")
        self.assertEqual(i18n.expected_source("docs/ru/README.md"), "README.md")
        self.assertEqual(i18n.expected_source("docs/ru/sub/a.md"), "docs/en/sub/a.md")
        self.assertIsNone(i18n.expected_source("docs/en/a.md"))


class CheckTests(RepoTestCase):
    def test_sources(self):
        self.write("docs/en/README.md", "# Not a source\n")
        self.assertEqual(
            i18n.english_sources(self.root), ["README.md", "docs/en/levels.md", "docs/en/usage.md"]
        )

    def test_current_draft_and_reviewed(self):
        self.translate("docs/ru/usage.md", "docs/en/usage.md")
        self.translate("docs/ru/levels.md", "docs/en/levels.md", status="reviewed", reviewers=["@alice"])
        entries = self.entries()
        self.assertEqual(entries["docs/ru/usage.md"].freshness, i18n.CURRENT)
        self.assertEqual(entries["docs/ru/usage.md"].bucket, "draft")
        self.assertEqual(entries["docs/ru/levels.md"].bucket, "reviewed")

    def test_outdated_when_source_changes(self):
        self.translate("docs/ru/usage.md", "docs/en/usage.md", status="reviewed")
        self.write("docs/en/usage.md", USAGE + "\nA new paragraph.\n")
        self.assertEqual(self.entries()["docs/ru/usage.md"].freshness, i18n.OUTDATED)

    def test_line_ending_change_is_not_outdated(self):
        self.translate("docs/ru/usage.md", "docs/en/usage.md")
        self.write("docs/en/usage.md", USAGE.replace("\n", "\r\n"))
        self.assertEqual(self.entries()["docs/ru/usage.md"].freshness, i18n.CURRENT)

    def test_missing_files(self):
        self.translate("docs/ru/usage.md", "docs/en/usage.md")
        entries = self.entries()
        self.assertEqual(entries["docs/ru/README.md"].freshness, i18n.MISSING)
        self.assertEqual(entries["docs/ru/levels.md"].freshness, i18n.MISSING)
        self.assertEqual(entries["docs/ru/levels.md"].source, "docs/en/levels.md")

    def test_invalid_without_header(self):
        self.write("docs/ru/usage.md", "# Использование\n")
        entry = self.entries()["docs/ru/usage.md"]
        self.assertEqual(entry.freshness, i18n.INVALID)
        self.assertIn("no i18n header", entry.detail)

    def test_invalid_malformed_header(self):
        self.write("docs/ru/usage.md", "<!--\ni18n:\n  source: docs/en/usage.md\n  status: final\n-->\n# Текст\n")
        self.assertEqual(self.entries()["docs/ru/usage.md"].freshness, i18n.INVALID)

    def test_invalid_when_source_does_not_match_path(self):
        self.translate("docs/ru/levels.md", "docs/en/usage.md")
        entries = self.entries()
        self.assertEqual(entries["docs/ru/levels.md"].freshness, i18n.INVALID)
        self.assertIn("file path matches docs/en/levels.md", entries["docs/ru/levels.md"].detail)
        self.assertEqual(entries["docs/ru/usage.md"].freshness, i18n.MISSING)

    def test_invalid_when_source_does_not_exist(self):
        self.translate("docs/ru/old.md", "docs/en/usage.md")
        self.write("docs/ru/old.md", self.read("docs/ru/old.md").replace("docs/en/usage.md", "docs/en/old.md"))
        self.assertEqual(self.entries()["docs/ru/old.md"].freshness, i18n.INVALID)

    def test_standalone_files_are_not_counted(self):
        self.write("docs/ru/glossary.md", "<!--\ni18n:\n  source: none\n  status: draft\n  reviewed_by: [@alice]\n-->\n# Глоссарий\n")
        self.write("docs/ru/notes.md", "# Заметки без заголовка\n")
        self.translate("docs/ru/usage.md", "docs/en/usage.md")
        report = i18n.collect(self.root)
        entries = {e.path: e for e in report.languages[0].entries}
        self.assertEqual(entries["docs/ru/glossary.md"].freshness, i18n.STANDALONE)
        self.assertEqual(entries["docs/ru/notes.md"].freshness, i18n.STANDALONE)
        counts = report.languages[0].counts()
        self.assertEqual(counts, {"reviewed": 0, "draft": 1, "outdated": 0, "missing": 2, "invalid": 0})
        self.assertFalse(report.has_invalid())
        self.assertEqual(report.languages[0].reviewers(), ["@alice"])

    def test_untranslated_copy(self):
        self.translate("docs/ru/usage.md", "docs/en/usage.md", body=USAGE)
        entry = self.entries()["docs/ru/usage.md"]
        self.assertEqual(entry.freshness, i18n.UNTRANSLATED)
        self.assertEqual(entry.bucket, "missing")

    def test_language_folder_detection(self):
        self.write("docs/img/readme.md", "# Images\n")
        self.write("docs/assets/a.md", "# Assets\n")
        self.write("docs/xx/usage.md", "# No header, unknown code\n")
        self.translate("docs/qq/usage.md", "docs/en/usage.md")
        self.write("docs/de/usage.md", "# Known code, no header\n")
        self.assertEqual(i18n.language_dirs(self.root), ["de", "qq"])

    def test_no_translations(self):
        code, out, _ = self.run_cli("check")
        self.assertEqual(code, 0)
        self.assertIn("No translations yet", out)

    def test_cli_strict_exit_code(self):
        self.write("docs/ru/usage.md", "# Без заголовка\n")
        self.assertEqual(self.run_cli("check")[0], 0)
        code, out, err = self.run_cli("check", "--strict")
        self.assertEqual(code, 1)
        self.assertIn("invalid", out)
        self.assertIn("invalid", err)

    def test_cli_strict_passes_with_outdated_files(self):
        self.translate("docs/ru/usage.md", "docs/en/usage.md", source_hash="000000000000")
        self.assertEqual(self.run_cli("check", "--strict")[0], 0)

    def test_cli_plain_table(self):
        self.translate("docs/ru/usage.md", "docs/en/usage.md")
        code, out, _ = self.run_cli("check")
        self.assertEqual(code, 0)
        self.assertIn("Русский (Russian)", out)
        self.assertRegex(out, r"docs/ru/usage\.md\s+draft\s+current")
        self.assertRegex(out, r"docs/ru/README\.md\s+-\s+missing")

    def test_cli_github_summary(self):
        self.translate("docs/ru/usage.md", "docs/en/usage.md")
        code, out, _ = self.run_cli("check", "--github-summary")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("## Translation status"))
        self.assertIn("| Русский (Russian) | `ru` | 0 | 1 | 0 | 2 | 0 |", out)
        self.assertIn("<details>", out)

    def test_cli_list_outdated(self):
        self.translate("docs/ru/usage.md", "docs/en/usage.md", source_hash="000000000000")
        self.translate("docs/ru/levels.md", "docs/en/levels.md")
        code, out, _ = self.run_cli("check", "--list-outdated")
        self.assertEqual(code, 0)
        lines = sorted(out.splitlines())
        self.assertEqual(
            lines,
            ["missing\tru\tdocs/ru/README.md\tREADME.md", "outdated\tru\tdocs/ru/usage.md\tdocs/en/usage.md"],
        )

    def test_cli_list_outdated_is_empty_when_current(self):
        self.translate("docs/ru/README.md", "README.md")
        self.translate("docs/ru/usage.md", "docs/en/usage.md")
        self.translate("docs/ru/levels.md", "docs/en/levels.md")
        self.assertEqual(self.run_cli("check", "--list-outdated")[1], "")


class StampTests(RepoTestCase):
    def test_stamp_adds_header_and_infers_source(self):
        self.write("docs/ru/usage.md", "# Использование\n\nТекст.\n")
        self.write("docs/ru/README.md", "# Проект\n")
        code, out, _ = self.run_cli("stamp", str(self.root / "docs/ru/usage.md"), str(self.root / "docs/ru/README.md"))
        self.assertEqual(code, 0, out)
        header = i18n.read_translation(self.root / "docs/ru/usage.md").header
        self.assertEqual(header.source, "docs/en/usage.md")
        self.assertEqual(header.source_hash, i18n.source_hash(self.root / "docs/en/usage.md"))
        self.assertEqual((header.status, header.translated_with, header.reviewed_by), ("draft", "ai", []))
        self.assertTrue(self.read("docs/ru/usage.md").endswith("-->\n\n# Использование\n\nТекст.\n"))
        self.assertEqual(i18n.read_translation(self.root / "docs/ru/README.md").header.source, "README.md")
        self.assertEqual(self.entries()["docs/ru/usage.md"].freshness, i18n.CURRENT)

    def test_stamp_refreshes_hash_and_resets_reviewed_status(self):
        self.translate("docs/ru/usage.md", "docs/en/usage.md", status="reviewed", reviewers=["@alice"])
        self.write("docs/en/usage.md", USAGE + "\nNew text.\n")
        code, out, _ = self.run_cli("stamp", str(self.root / "docs/ru/usage.md"))
        self.assertEqual(code, 0)
        self.assertIn("reviewed to draft", out)
        header = i18n.read_translation(self.root / "docs/ru/usage.md").header
        self.assertEqual(header.source_hash, i18n.source_hash(self.root / "docs/en/usage.md"))
        self.assertEqual(header.status, "draft")
        self.assertEqual(header.reviewed_by, ["@alice"])

    def test_stamp_keeps_status_when_source_did_not_change(self):
        self.translate("docs/ru/usage.md", "docs/en/usage.md", status="reviewed", reviewers=["@alice"])
        before = self.read("docs/ru/usage.md")
        code, out, _ = self.run_cli("stamp", str(self.root / "docs/ru/usage.md"))
        self.assertEqual(code, 0)
        self.assertIn("no change", out)
        self.assertEqual(self.read("docs/ru/usage.md"), before)

    def test_stamp_reviewed_merges_reviewers(self):
        self.translate("docs/ru/usage.md", "docs/en/usage.md", reviewers=["@alice"])
        code, _, _ = self.run_cli(
            "stamp", str(self.root / "docs/ru/usage.md"), "--status", "reviewed",
            "--reviewer", "@bob", "--reviewer", "carol,@ALICE", "--translated-with", "human",
        )
        self.assertEqual(code, 0)
        header = i18n.read_translation(self.root / "docs/ru/usage.md").header
        self.assertEqual(header.status, "reviewed")
        self.assertEqual(header.translated_with, "human")
        self.assertEqual(header.reviewed_by, ["@alice", "@bob", "@carol"])

    def test_stamp_relative_path_from_root(self):
        self.write("docs/ru/levels.md", "# Уровни\n")
        self.assertEqual(self.run_cli("stamp", "docs/ru/levels.md")[0], 0)
        self.assertIsNotNone(i18n.read_translation(self.root / "docs/ru/levels.md").header)

    def test_stamp_source_none(self):
        self.write("docs/ru/glossary.md", "# Глоссарий\n")
        code, _, err = self.run_cli("stamp", str(self.root / "docs/ru/glossary.md"))
        self.assertEqual(code, 1)
        self.assertIn("--source none", err)
        code, _, _ = self.run_cli("stamp", str(self.root / "docs/ru/glossary.md"), "--source", "none")
        self.assertEqual(code, 0)
        header = i18n.read_translation(self.root / "docs/ru/glossary.md").header
        self.assertTrue(header.standalone)
        self.assertIsNone(header.translated_with)
        # A second stamp keeps "source: none" without the option.
        code, _, _ = self.run_cli("stamp", str(self.root / "docs/ru/glossary.md"), "--status", "reviewed", "--reviewer", "@alice")
        self.assertEqual(code, 0)
        header = i18n.read_translation(self.root / "docs/ru/glossary.md").header
        self.assertEqual((header.source, header.status), ("none", "reviewed"))

    def test_stamp_repairs_malformed_header(self):
        self.write("docs/ru/usage.md", "<!--\ni18n:\n  source: docs/en/usage.md\n  status: final\n-->\n\n# Текст\n")
        self.assertEqual(self.run_cli("stamp", str(self.root / "docs/ru/usage.md"))[0], 0)
        self.assertEqual(self.entries()["docs/ru/usage.md"].freshness, i18n.CURRENT)
        self.assertEqual(self.read("docs/ru/usage.md").count("i18n:"), 1)

    def test_stamp_rejects_files_outside_language_folders(self):
        for rel in ("docs/en/usage.md", "README.md"):
            code, _, err = self.run_cli("stamp", str(self.root / rel))
            self.assertEqual(code, 1, rel)
            self.assertIn("docs/<lang>/", err)

    def test_stamp_rejects_bad_reviewer(self):
        self.write("docs/ru/usage.md", "# Текст\n")
        code, _, err = self.run_cli("stamp", str(self.root / "docs/ru/usage.md"), "--reviewer", "not valid!")
        self.assertEqual(code, 1)
        self.assertIn("GitHub handle", err)

    def test_stamp_keeps_crlf_line_endings(self):
        self.write("docs/ru/usage.md", "# Текст\r\n\r\nАбзац.\r\n")
        self.run_cli("stamp", str(self.root / "docs/ru/usage.md"))
        text = self.read("docs/ru/usage.md")
        self.assertNotIn("\n", text.replace("\r\n", ""))
        self.assertTrue(text.startswith("<!--\r\ni18n:\r\n"))


class TableTests(RepoTestCase):
    def test_table_regenerates_only_the_block(self):
        self.write("docs/LANGUAGES.md", LANGUAGES)
        self.translate("docs/ru/README.md", "README.md", status="reviewed", reviewers=["@alice"])
        self.translate("docs/ru/usage.md", "docs/en/usage.md", source_hash="000000000000")
        code, out, _ = self.run_cli("table")
        self.assertEqual(code, 0)
        self.assertIn("updated", out)
        text = self.read("docs/LANGUAGES.md")
        self.assertTrue(text.startswith("# Languages\n\nIntro text.\n\n<!-- i18n-table:start -->\n"))
        self.assertTrue(text.endswith("<!-- i18n-table:end -->\n\nFooter text.\n"))
        self.assertNotIn("old table", text)
        self.assertIn("Each language has 3 files to translate.", text)
        self.assertIn("| Language | Code | Reviewed | Draft | Outdated | Missing | Reviewed by |", text)
        self.assertIn("| [Русский (Russian)](ru/README.md) | `ru` | 1 | 0 | 1 | 1 | @alice |", text)
        # A second run makes no change.
        self.assertIn("no change", self.run_cli("table")[1])

    def test_table_shows_invalid_column_only_when_needed(self):
        self.write("docs/LANGUAGES.md", LANGUAGES)
        self.write("docs/de/usage.md", "# Ohne Kopfzeile\n")
        self.run_cli("table")
        text = self.read("docs/LANGUAGES.md")
        self.assertIn("| Invalid |", text)
        self.assertIn("| Deutsch (German) | `de` | 0 | 0 | 0 | 2 | 1 | — |", text)

    def test_table_without_languages(self):
        self.write("docs/LANGUAGES.md", LANGUAGES)
        self.run_cli("table")
        self.assertIn("No translations yet.", self.read("docs/LANGUAGES.md"))

    def test_table_requires_markers(self):
        self.write("docs/LANGUAGES.md", "# Languages\n")
        code, _, err = self.run_cli("table")
        self.assertEqual(code, 1)
        self.assertIn("i18n-table:start", err)

    def test_table_requires_file(self):
        code, _, err = self.run_cli("table")
        self.assertEqual(code, 1)
        self.assertIn("LANGUAGES.md", err)


class NewTests(RepoTestCase):
    def test_new_scaffolds_each_source(self):
        code, out, _ = self.run_cli("new", "de")
        self.assertEqual(code, 0)
        for rel, source in (("docs/de/README.md", "README.md"), ("docs/de/usage.md", "docs/en/usage.md"), ("docs/de/levels.md", "docs/en/levels.md")):
            self.assertIn("created %s" % rel, out)
            header = i18n.read_translation(self.root / rel).header
            self.assertEqual(header.source, source)
            self.assertEqual(header.status, "draft")
            self.assertEqual(header.source_hash, i18n.source_hash(self.root / source))
        self.assertTrue(self.read("docs/de/usage.md").endswith("-->\n\n" + USAGE))

    def test_new_files_are_untranslated(self):
        self.run_cli("new", "de")
        entries = self.entries("de")
        self.assertEqual({e.freshness for e in entries.values()}, {i18n.UNTRANSLATED})
        self.assertEqual(i18n.collect(self.root).languages[0].counts()["missing"], 3)

    def test_new_rebases_readme_links(self):
        self.write("README.md", README + "\n![logo](docs/assets/logo.png)\n[ref]: CONTRIBUTING.md\n<img src=\"docs/en/pic.png\">\n```\n[x](LICENSE)\n```\n[web](https://example.com) [top](#project)\n")
        self.run_cli("new", "de")
        text = self.read("docs/de/README.md")
        self.assertIn("[Русский](../ru/README.md)", text)
        self.assertIn("[usage](usage.md)", text)
        self.assertIn("[license](../../LICENSE)", text)
        self.assertIn("![logo](../assets/logo.png)", text)
        self.assertIn("[ref]: ../../CONTRIBUTING.md", text)
        self.assertIn('<img src="../en/pic.png">', text)
        self.assertIn("```\n[x](LICENSE)\n```", text)
        self.assertIn("[web](https://example.com) [top](#project)", text)

    def test_new_refuses_existing_folder(self):
        self.write("docs/de/usage.md", "# Schon da\n")
        code, _, err = self.run_cli("new", "de")
        self.assertEqual(code, 1)
        self.assertIn("already exists", err)
        self.assertEqual(self.read("docs/de/usage.md"), "# Schon da\n")

    def test_new_rejects_bad_codes(self):
        for code_arg in ("en", "German", "d"):
            code, _, err = self.run_cli("new", code_arg)
            self.assertEqual(code, 1, code_arg)
            self.assertTrue(err.startswith("error:"))
        self.assertFalse((self.root / "docs/German").exists())

    def test_new_supports_region_codes(self):
        self.assertEqual(self.run_cli("new", "pt-BR")[0], 0)
        self.assertTrue((self.root / "docs/pt-BR/usage.md").is_file())


if __name__ == "__main__":
    unittest.main()
