#!/usr/bin/env python3
"""Track the freshness of the documentation translations.

English is the source language. The English sources are ``README.md`` (in
the repository root) and each ``docs/en/**/*.md`` file:

    README.md          ->  docs/<lang>/README.md
    docs/en/<name>.md  ->  docs/<lang>/<name>.md

Each translation starts with an i18n header. The header is an HTML comment,
so GitHub does not show it::

    <!--
    i18n:
      source: docs/en/usage.md
      source_hash: 1a2b3c4d5e6f
      status: draft
      translated_with: ai
      reviewed_by: []
    -->

``source_hash`` is the first 12 hex characters of the SHA-256 hash of the
English source, after the line endings are changed to ``\\n``. A file that
is not a translation (for example ``docs/<lang>/glossary.md``) uses
``source: none``. The tool does not count these files.

Commands:

    check   Show the status of each translation.
    stamp   Write or refresh the i18n header of translation files.
    table   Regenerate the status table in docs/LANGUAGES.md.
    new     Make a language folder with English copies to translate.

The tool needs Python 3.8 or later and no other packages.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

SOURCE_LANG = "en"
SOURCE_README = "README.md"
DOCS_DIR = "docs"
LANGUAGES_FILE = "docs/LANGUAGES.md"
HASH_LENGTH = 12
NO_SOURCE = "none"
STATUSES = ("draft", "reviewed")
TRANSLATED_WITH = ("ai", "human")
TABLE_START = "<!-- i18n-table:start -->"
TABLE_END = "<!-- i18n-table:end -->"

# Freshness of one file in a language folder.
CURRENT = "current"
OUTDATED = "outdated"
MISSING = "missing"
UNTRANSLATED = "untranslated"
INVALID = "invalid"
STANDALONE = "standalone"

# Freshness values that tell a translator to update a file.
NEEDS_UPDATE = (OUTDATED, MISSING, UNTRANSLATED)

# Counters in the summaries and in the status table.
BUCKETS = ("reviewed", "draft", "outdated", "missing", "invalid")

LANG_CODE_RE = re.compile(r"^[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
HASH_RE = re.compile(r"^[0-9a-f]{%d}$" % HASH_LENGTH)
HANDLE_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")
FIELD_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$")

# Native name and English name of each language.
LANGUAGE_NAMES: Dict[str, Tuple[str, str]] = {
    "ar": ("العربية", "Arabic"),
    "bg": ("Български", "Bulgarian"),
    "bn": ("বাংলা", "Bengali"),
    "ca": ("Català", "Catalan"),
    "cs": ("Čeština", "Czech"),
    "da": ("Dansk", "Danish"),
    "de": ("Deutsch", "German"),
    "el": ("Ελληνικά", "Greek"),
    "en": ("English", "English"),
    "es": ("Español", "Spanish"),
    "et": ("Eesti", "Estonian"),
    "fa": ("فارسی", "Persian"),
    "fi": ("Suomi", "Finnish"),
    "fr": ("Français", "French"),
    "he": ("עברית", "Hebrew"),
    "hi": ("हिन्दी", "Hindi"),
    "hr": ("Hrvatski", "Croatian"),
    "hu": ("Magyar", "Hungarian"),
    "hy": ("Հայերեն", "Armenian"),
    "id": ("Bahasa Indonesia", "Indonesian"),
    "it": ("Italiano", "Italian"),
    "ja": ("日本語", "Japanese"),
    "ka": ("ქართული", "Georgian"),
    "kk": ("Қазақ тілі", "Kazakh"),
    "ko": ("한국어", "Korean"),
    "lt": ("Lietuvių", "Lithuanian"),
    "lv": ("Latviešu", "Latvian"),
    "ms": ("Bahasa Melayu", "Malay"),
    "nb": ("Norsk bokmål", "Norwegian Bokmål"),
    "nl": ("Nederlands", "Dutch"),
    "pl": ("Polski", "Polish"),
    "pt": ("Português", "Portuguese"),
    "pt-BR": ("Português (Brasil)", "Portuguese (Brazil)"),
    "ro": ("Română", "Romanian"),
    "ru": ("Русский", "Russian"),
    "sk": ("Slovenčina", "Slovak"),
    "sl": ("Slovenščina", "Slovenian"),
    "sr": ("Српски", "Serbian"),
    "sv": ("Svenska", "Swedish"),
    "th": ("ไทย", "Thai"),
    "tr": ("Türkçe", "Turkish"),
    "uk": ("Українська", "Ukrainian"),
    "uz": ("Oʻzbekcha", "Uzbek"),
    "vi": ("Tiếng Việt", "Vietnamese"),
    "zh": ("中文", "Chinese"),
    "zh-Hans": ("简体中文", "Chinese (Simplified)"),
    "zh-Hant": ("繁體中文", "Chinese (Traditional)"),
}


class ToolError(Exception):
    """An error that the user can correct. The CLI prints it and exits 1."""


# --------------------------------------------------------------------------
# Languages and paths
# --------------------------------------------------------------------------


def default_root() -> Path:
    """Return the repository root: the parent of the ``tools/`` folder."""
    return Path(__file__).resolve().parent.parent


def _language_entry(code: str) -> Optional[Tuple[str, str]]:
    return LANGUAGE_NAMES.get(code) or LANGUAGE_NAMES.get(code.split("-")[0])


def language_name(code: str) -> str:
    """Return the native name of a language, or the code if it is unknown."""
    if code in LANGUAGE_NAMES:
        return LANGUAGE_NAMES[code][0]
    entry = _language_entry(code)
    if entry is None:
        return code
    return "%s (%s)" % (entry[0], code)


def language_label(code: str) -> str:
    """Return "Native (English)", for example "Русский (Russian)"."""
    entry = LANGUAGE_NAMES.get(code)
    if entry is None:
        return language_name(code)
    native, english = entry
    return native if native == english else "%s (%s)" % (native, english)


def is_language_code(code: str) -> bool:
    return bool(LANG_CODE_RE.match(code))


def translation_path(source: str, lang: str) -> str:
    """Return the path of the translation of an English source."""
    if source == SOURCE_README:
        return "%s/%s/README.md" % (DOCS_DIR, lang)
    prefix = "%s/%s/" % (DOCS_DIR, SOURCE_LANG)
    if not source.startswith(prefix):
        raise ValueError("not an English source: %s" % source)
    return "%s/%s/%s" % (DOCS_DIR, lang, source[len(prefix):])


def expected_source(path: str) -> Optional[str]:
    """Return the English source that matches a path in a language folder."""
    parts = path.split("/")
    if len(parts) < 3 or parts[0] != DOCS_DIR or parts[1] == SOURCE_LANG:
        return None
    inner = "/".join(parts[2:])
    if inner == "README.md":
        return SOURCE_README
    return "%s/%s/%s" % (DOCS_DIR, SOURCE_LANG, inner)


def english_sources(root: Path) -> List[str]:
    """Return the English sources: README.md first, then docs/en/**/*.md.

    ``docs/en/README.md`` is not a source, because ``docs/<lang>/README.md``
    translates the root ``README.md``.
    """
    sources: List[str] = []
    if (root / SOURCE_README).is_file():
        sources.append(SOURCE_README)
    en_dir = root / DOCS_DIR / SOURCE_LANG
    if en_dir.is_dir():
        skip = "%s/%s/README.md" % (DOCS_DIR, SOURCE_LANG)
        for path in sorted(en_dir.rglob("*.md")):
            rel = path.relative_to(root).as_posix()
            if rel != skip and path.is_file():
                sources.append(rel)
    return sources


def language_dirs(root: Path) -> List[str]:
    """Return the codes of the language folders in docs/ (not "en").

    A folder is a language folder if its name is a language code, it has
    Markdown files, and the code is known or a file has an i18n header.
    """
    docs = root / DOCS_DIR
    if not docs.is_dir():
        return []
    codes: List[str] = []
    for folder in sorted(docs.iterdir()):
        name = folder.name
        if not folder.is_dir() or name == SOURCE_LANG or not is_language_code(name):
            continue
        files = [p for p in folder.rglob("*.md") if p.is_file()]
        if not files:
            continue
        if _language_entry(name) is not None or any(
            read_translation(p).block is not None for p in files
        ):
            codes.append(name)
    return codes


# --------------------------------------------------------------------------
# Files and hashes
# --------------------------------------------------------------------------


def hash_bytes(data: bytes) -> str:
    """Return the source hash of some file content."""
    data = data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return hashlib.sha256(data).hexdigest()[:HASH_LENGTH]


def source_hash(path: Path) -> str:
    """Return the source hash of a file."""
    return hash_bytes(Path(path).read_bytes())


def read_text(path: Path) -> str:
    """Read a UTF-8 file and keep its line endings."""
    with open(str(path), encoding="utf-8", newline="") as handle:
        return handle.read()


def write_text(path: Path, text: str) -> None:
    """Write a UTF-8 file and keep the line endings of ``text``."""
    with open(str(path), "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


def _newline_of(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def _normalize(text: str) -> str:
    return text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n").strip()


# --------------------------------------------------------------------------
# The i18n header
# --------------------------------------------------------------------------


@dataclass
class Header:
    source: str
    source_hash: Optional[str] = None
    status: str = "draft"
    translated_with: Optional[str] = None
    reviewed_by: List[str] = field(default_factory=list)

    @property
    def standalone(self) -> bool:
        return self.source == NO_SOURCE

    def render(self, newline: str = "\n") -> str:
        lines = ["<!--", "i18n:", "  source: %s" % self.source]
        if not self.standalone:
            lines.append("  source_hash: %s" % self.source_hash)
        lines.append("  status: %s" % self.status)
        if self.translated_with:
            lines.append("  translated_with: %s" % self.translated_with)
        lines.append("  reviewed_by: [%s]" % ", ".join(self.reviewed_by))
        lines.append("-->")
        return newline.join(lines) + newline


@dataclass
class HeaderBlock:
    """The position and the raw fields of an i18n header in a file."""

    start: int  # index of the "<!--" line
    end: int  # index of the "-->" line, or -1 if the comment is not closed
    fields: Dict[str, object]
    errors: List[str]


@dataclass
class ParsedFile:
    lines: List[str]
    block: Optional[HeaderBlock]
    header: Optional[Header]
    errors: List[str]

    def text_without_header(self) -> str:
        if self.block is None or self.block.end < 0:
            return "".join(self.lines)
        return "".join(self.lines[: self.block.start] + self.lines[self.block.end + 1 :])


def _clean_line(line: str) -> str:
    return line.strip().lstrip("﻿").strip()


def _front_matter_end(lines: Sequence[str]) -> int:
    """Return the index of the first line after YAML front matter (0 if none)."""
    if lines and _clean_line(lines[0]) == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() in ("---", "..."):
                return index + 1
    return 0


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
        return value[1:-1]
    return value


def normalize_handle(handle: str) -> str:
    """Return a GitHub handle with one leading "@"."""
    return "@" + _unquote(handle).strip().lstrip("@")


def valid_handle(handle: str) -> bool:
    return bool(HANDLE_RE.match(normalize_handle(handle)[1:]))


def find_header(lines: Sequence[str]) -> Optional[HeaderBlock]:
    """Find the i18n header at the top of a file (after front matter, if any).

    Return None if the file has no i18n header.
    """
    index = _front_matter_end(lines)
    while index < len(lines) and not _clean_line(lines[index]):
        index += 1
    if index + 1 >= len(lines):
        return None
    if _clean_line(lines[index]) != "<!--" or lines[index + 1].strip() != "i18n:":
        return None

    start = index
    end = -1
    errors: List[str] = []
    for pos in range(start + 2, len(lines)):
        if "-->" in lines[pos]:
            end = pos
            if lines[pos].strip() != "-->":
                errors.append('put "-->" on a separate line')
            break
    if end < 0:
        errors.append('the header comment has no closing "-->"')
        return HeaderBlock(start, -1, {}, errors)

    fields: Dict[str, object] = {}
    list_key: Optional[str] = None
    for raw in lines[start + 2 : end]:
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        if text.startswith("-") and list_key is not None:
            items = fields[list_key]
            assert isinstance(items, list)
            items.append(_unquote(text[1:]))
            continue
        match = FIELD_RE.match(text)
        if not match:
            errors.append("cannot read the header line %r" % text)
            continue
        key, value = match.group(1), match.group(2).strip()
        list_key = None
        if key == "reviewed_by":
            if not value:
                fields[key] = []
                list_key = key
            elif value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                fields[key] = [_unquote(v) for v in inner.split(",") if v.strip()]
            else:
                errors.append("reviewed_by must be a list, for example [@handle]")
        else:
            fields[key] = _unquote(value)
    return HeaderBlock(start, end, fields, errors)


def header_from_fields(fields: Dict[str, object]) -> Tuple[Optional[Header], List[str]]:
    """Make a Header from raw fields. Return (header or None, errors)."""
    errors: List[str] = []
    source = str(fields.get("source") or "")
    if not source:
        errors.append("the header has no 'source'")
    standalone = source == NO_SOURCE

    hash_value = fields.get("source_hash")
    if not standalone:
        if not hash_value:
            errors.append("the header has no 'source_hash'")
        elif not HASH_RE.match(str(hash_value)):
            errors.append("'source_hash' must be %d lowercase hex characters" % HASH_LENGTH)

    status = fields.get("status")
    if not status:
        errors.append("the header has no 'status'")
    elif status not in STATUSES:
        errors.append("'status' must be draft or reviewed, not %r" % status)

    translated_with = fields.get("translated_with")
    if translated_with is None or translated_with == "":
        if not standalone:
            errors.append("the header has no 'translated_with'")
        translated_with = None
    elif translated_with not in TRANSLATED_WITH:
        errors.append("'translated_with' must be ai or human, not %r" % translated_with)

    raw_reviewers = fields.get("reviewed_by", [])
    reviewers: List[str] = []
    if not isinstance(raw_reviewers, list):
        errors.append("reviewed_by must be a list, for example [@handle]")
    else:
        for item in raw_reviewers:
            if valid_handle(str(item)):
                reviewers.append(normalize_handle(str(item)))
            else:
                errors.append("%r in reviewed_by is not a GitHub handle" % item)

    if errors:
        return None, errors
    header = Header(
        source=source,
        source_hash=None if standalone else str(hash_value),
        status=str(status),
        translated_with=str(translated_with) if translated_with else None,
        reviewed_by=reviewers,
    )
    return header, []


def parse_text(text: str) -> ParsedFile:
    lines = text.splitlines(keepends=True)
    block = find_header(lines)
    if block is None:
        return ParsedFile(lines, None, None, ["no i18n header"])
    if block.errors:
        return ParsedFile(lines, block, None, list(block.errors))
    header, errors = header_from_fields(block.fields)
    return ParsedFile(lines, block, header, errors)


def read_translation(path: Path) -> ParsedFile:
    return parse_text(read_text(path))


def with_header(lines: Sequence[str], block: Optional[HeaderBlock], header: Header, newline: str) -> str:
    """Return the file text with ``header`` in place of the old header."""
    rendered = header.render(newline)
    if block is not None:
        if block.end < 0:
            raise ToolError('the i18n header has no closing "-->". Correct the header by hand.')
        return "".join(lines[: block.start]) + rendered + "".join(lines[block.end + 1 :])

    start = _front_matter_end(lines)
    head = list(lines[:start])
    rest = list(lines[start:])
    bom = ""
    if start == 0 and rest and rest[0].startswith("﻿"):
        bom = "﻿"
        rest[0] = rest[0][1:]
    gap = "" if not rest or not rest[0].strip() else newline
    return bom + "".join(head) + rendered + gap + "".join(rest)


# --------------------------------------------------------------------------
# README links
# --------------------------------------------------------------------------

_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
_INLINE_LINK_RE = re.compile(r"(\]\(\s*<?)([^)\s>]+)")
_REF_DEF_RE = re.compile(r"^(\s{0,3}\[[^\]]+\]:\s*<?)([^\s>]+)")
_HTML_ATTR_RE = re.compile(r"(\b(?:href|src)\s*=\s*\")([^\"]+)(\")")


def rebase_link(target: str, sources: Iterable[str]) -> str:
    """Change a relative link of the root README.md for docs/<lang>/README.md."""
    if not target or target.startswith(("#", "/", "\\")) or _SCHEME_RE.match(target):
        return target
    path, sep, fragment = target.partition("#")
    clean = path[2:] if path.startswith("./") else path
    if not clean:
        return target
    en_prefix = "%s/%s/" % (DOCS_DIR, SOURCE_LANG)
    if clean == SOURCE_README:
        new = "README.md"
    elif clean.startswith(en_prefix):
        rest = clean[len(en_prefix):]
        new = rest if clean in set(sources) else "../%s/%s" % (SOURCE_LANG, rest)
    elif clean.startswith(DOCS_DIR + "/"):
        new = "../" + clean[len(DOCS_DIR) + 1 :]
    else:
        new = "../../" + clean
    return new + sep + fragment


def rebase_readme_links(text: str, sources: Iterable[str]) -> str:
    """Change the relative links of README.md so that they work in docs/<lang>/.

    The function does not change links in fenced code blocks.
    """
    source_list = list(sources)
    out: List[str] = []
    fence: Optional[str] = None
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if fence is not None:
            if stripped.startswith(fence):
                fence = None
            out.append(line)
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            fence = stripped[:3]
            out.append(line)
            continue
        line = _INLINE_LINK_RE.sub(
            lambda m: m.group(1) + rebase_link(m.group(2), source_list), line
        )
        line = _REF_DEF_RE.sub(lambda m: m.group(1) + rebase_link(m.group(2), source_list), line)
        line = _HTML_ATTR_RE.sub(
            lambda m: m.group(1) + rebase_link(m.group(2), source_list) + m.group(3), line
        )
        out.append(line)
    return "".join(out)


# --------------------------------------------------------------------------
# Status report
# --------------------------------------------------------------------------


@dataclass
class Entry:
    lang: str
    path: str
    source: Optional[str]
    freshness: str
    status: Optional[str] = None
    translated_with: Optional[str] = None
    reviewers: List[str] = field(default_factory=list)
    detail: str = ""

    @property
    def bucket(self) -> Optional[str]:
        if self.freshness == CURRENT:
            return "reviewed" if self.status == "reviewed" else "draft"
        if self.freshness == OUTDATED:
            return "outdated"
        if self.freshness in (MISSING, UNTRANSLATED):
            return "missing"
        if self.freshness == INVALID:
            return "invalid"
        return None


@dataclass
class LanguageReport:
    code: str
    entries: List[Entry]

    def counts(self) -> Dict[str, int]:
        counts = dict.fromkeys(BUCKETS, 0)
        for entry in self.entries:
            if entry.bucket:
                counts[entry.bucket] += 1
        return counts

    def reviewers(self) -> List[str]:
        seen: Dict[str, str] = {}
        for entry in self.entries:
            for handle in entry.reviewers:
                seen.setdefault(handle.lower(), handle)
        return [seen[key] for key in sorted(seen)]


@dataclass
class Report:
    root: Path
    sources: List[str]
    languages: List[LanguageReport]
    notes: List[str] = field(default_factory=list)

    def entries(self) -> List[Entry]:
        return [entry for lang in self.languages for entry in lang.entries]

    def has_invalid(self) -> bool:
        return any(entry.freshness == INVALID for entry in self.entries())


def _is_untranslated(root: Path, parsed: ParsedFile, source: str, sources: List[str]) -> bool:
    body = _normalize(parsed.text_without_header())
    original = read_text(root / source)
    if body == _normalize(original):
        return True
    return source == SOURCE_README and body == _normalize(rebase_readme_links(original, sources))


def _check_language(root: Path, code: str, sources: List[str], hashes: Dict[str, str]) -> LanguageReport:
    source_set = set(sources)
    entries: List[Entry] = []
    covered = set()
    folder = root / DOCS_DIR / code
    for path in sorted(folder.rglob("*.md")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        expected = expected_source(rel)
        expected_ok = expected in source_set
        parsed = read_translation(path)

        if parsed.block is None:
            if expected_ok:
                covered.add(expected)
                entries.append(Entry(code, rel, expected, INVALID, detail="no i18n header"))
            else:
                entries.append(
                    Entry(code, rel, None, STANDALONE, detail="no English source, no i18n header")
                )
            continue

        header = parsed.header
        if header is None:
            if expected_ok:
                covered.add(expected)
            entries.append(
                Entry(code, rel, expected if expected_ok else None, INVALID, detail="; ".join(parsed.errors))
            )
            continue

        info = dict(status=header.status, translated_with=header.translated_with, reviewers=header.reviewed_by)
        if header.standalone:
            entries.append(Entry(code, rel, None, STANDALONE, **info))
            continue

        problem = ""
        if header.source not in source_set:
            problem = "the source %s is not an English source" % header.source
        elif expected_ok and header.source != expected:
            problem = "the source is %s, but the file path matches %s" % (header.source, expected)
        elif header.source in covered:
            problem = "another file already translates %s" % header.source
        if problem:
            if expected_ok:
                covered.add(expected)
            entries.append(Entry(code, rel, header.source, INVALID, detail=problem, **info))
            continue

        covered.add(header.source)
        if header.source_hash != hashes[header.source]:
            freshness = OUTDATED
        elif _is_untranslated(root, parsed, header.source, sources):
            freshness = UNTRANSLATED
        else:
            freshness = CURRENT
        entries.append(Entry(code, rel, header.source, freshness, **info))

    for source in sources:
        if source not in covered:
            entries.append(Entry(code, translation_path(source, code), source, MISSING))

    order = {source: index for index, source in enumerate(sources)}

    def sort_key(entry: Entry) -> Tuple[int, int, str]:
        if entry.source in order:
            return (0, order[entry.source], entry.path)
        return (1, 0, entry.path)

    entries.sort(key=sort_key)
    return LanguageReport(code, entries)


def collect(root: Path) -> Report:
    """Read the English sources and all language folders."""
    root = Path(root)
    sources = english_sources(root)
    hashes = {source: source_hash(root / source) for source in sources}
    notes: List[str] = []
    if (root / DOCS_DIR / SOURCE_LANG / "README.md").is_file():
        notes.append(
            "docs/en/README.md is not a source. docs/<lang>/README.md translates the root README.md."
        )
    languages = [_check_language(root, code, sources, hashes) for code in language_dirs(root)]
    return Report(root, sources, languages, notes)


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------


def _md(text: str) -> str:
    return text.replace("|", "\\|")


def _freshness_text(entry: Entry) -> str:
    return "%s (%s)" % (entry.freshness, entry.detail) if entry.detail else entry.freshness


def _counts_text(counts: Dict[str, int]) -> str:
    return ", ".join("%d %s" % (counts[name], name) for name in BUCKETS)


def format_check(report: Report) -> str:
    out = ["English sources: %d file(s). English is the source language." % len(report.sources)]
    out.extend("Note: %s" % note for note in report.notes)
    if not report.languages:
        out.append("No translations yet. To add a language, run: python3 tools/i18n_status.py new LANG")
        return "\n".join(out) + "\n"
    for lang in report.languages:
        out.append("")
        out.append("%s  %s" % (lang.code, language_label(lang.code)))
        rows = [("FILE", "STATUS", "FRESHNESS")]
        rows.extend((e.path, e.status or "-", _freshness_text(e)) for e in lang.entries)
        width0 = max(len(row[0]) for row in rows)
        width1 = max(len(row[1]) for row in rows)
        for row in rows:
            out.append("  %s  %s  %s" % (row[0].ljust(width0), row[1].ljust(width1), row[2]))
        out.append("  Total: %s" % _counts_text(lang.counts()))
    return "\n".join(out) + "\n"


def format_github_summary(report: Report) -> str:
    out = ["## Translation status", ""]
    out.append("English is the source language. It has %d source files." % len(report.sources))
    for note in report.notes:
        out.extend(["", "> Note: %s" % _md(note)])
    if not report.languages:
        out.extend(["", "No translations yet."])
        return "\n".join(out) + "\n"
    out.extend(
        [
            "",
            "| Language | Code | Reviewed | Draft | Outdated | Missing | Invalid |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for lang in report.languages:
        c = lang.counts()
        out.append(
            "| %s | `%s` | %d | %d | %d | %d | %d |"
            % (language_label(lang.code), lang.code, c["reviewed"], c["draft"], c["outdated"], c["missing"], c["invalid"])
        )
    for lang in report.languages:
        out.extend(
            [
                "",
                "<details><summary><code>%s</code> %s: files</summary>" % (lang.code, language_label(lang.code)),
                "",
                "| File | Status | Freshness |",
                "| --- | --- | --- |",
            ]
        )
        for entry in lang.entries:
            out.append(
                "| `%s` | %s | %s |" % (entry.path, entry.status or "-", _md(_freshness_text(entry)))
            )
        out.extend(["", "</details>"])
    return "\n".join(out) + "\n"


def format_list_outdated(report: Report) -> str:
    """Return one tab-separated line for each file that needs an update.

    Fields: freshness, language code, translation path, English source.
    Freshness is outdated, missing, or untranslated.
    """
    lines = []
    for lang in report.languages:
        for entry in lang.entries:
            if entry.freshness in NEEDS_UPDATE:
                lines.append("\t".join([entry.freshness, lang.code, entry.path, entry.source or ""]))
    return "".join(line + "\n" for line in lines)


def render_languages_table(report: Report) -> str:
    """Return the content of the generated block in docs/LANGUAGES.md."""
    out = [
        "<!-- Generated by `python3 tools/i18n_status.py table`. Do not edit this block. -->",
        "",
        "English (`en`) is the source language. Each language has %d files to translate."
        % len(report.sources),
        "",
    ]
    if not report.languages:
        out.append("No translations yet.")
        return "\n".join(out)
    show_invalid = any(lang.counts()["invalid"] for lang in report.languages)
    columns = ["Language", "Code", "Reviewed", "Draft", "Outdated", "Missing"]
    if show_invalid:
        columns.append("Invalid")
    columns.append("Reviewed by")
    out.append("| " + " | ".join(columns) + " |")
    out.append("| " + " | ".join(["---", "---"] + ["---:"] * (len(columns) - 3) + ["---"]) + " |")
    for lang in report.languages:
        counts = lang.counts()
        label = language_label(lang.code)
        if (report.root / translation_path(SOURCE_README, lang.code)).is_file():
            label = "[%s](%s/README.md)" % (label, lang.code)
        cells = [label, "`%s`" % lang.code] + [
            str(counts[name]) for name in ("reviewed", "draft", "outdated", "missing")
        ]
        if show_invalid:
            cells.append(str(counts["invalid"]))
        cells.append(", ".join(lang.reviewers()) or "—")
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------


def update_languages_table(root: Path) -> bool:
    """Regenerate the table in docs/LANGUAGES.md. Return True if it changed."""
    path = root / LANGUAGES_FILE
    if not path.is_file():
        raise ToolError("%s does not exist" % LANGUAGES_FILE)
    text = read_text(path)
    start = text.find(TABLE_START)
    end = text.find(TABLE_END)
    if start < 0 or end < 0 or end < start:
        raise ToolError(
            "%s must contain the lines %s and %s, in this order" % (LANGUAGES_FILE, TABLE_START, TABLE_END)
        )
    newline = _newline_of(text)
    block = render_languages_table(collect(root)).replace("\n", newline)
    new_text = (
        text[: start + len(TABLE_START)] + newline + newline + block + newline + newline + text[end:]
    )
    if new_text == text:
        return False
    write_text(path, new_text)
    return True


def _resolve_in_root(root: Path, arg: str) -> str:
    path = Path(arg)
    if not path.is_absolute():
        in_root = root / path
        path = in_root if in_root.exists() else Path.cwd() / path
    if not path.is_file():
        raise ToolError("%s: the file does not exist" % arg)
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        raise ToolError("%s: the file is not in %s" % (arg, root))


def _merge_handles(*groups: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for group in groups:
        for handle in group:
            handle = normalize_handle(handle)
            if handle.lower() not in seen:
                seen.add(handle.lower())
                result.append(handle)
    return result


def stamp_file(
    root: Path,
    file_arg: str,
    status: Optional[str] = None,
    reviewers: Sequence[str] = (),
    translated_with: Optional[str] = None,
    source: Optional[str] = None,
) -> List[str]:
    """Write or refresh the i18n header of one file. Return messages."""
    root = Path(root)
    rel = _resolve_in_root(root, file_arg)
    parts = rel.split("/")
    if (
        len(parts) < 3
        or parts[0] != DOCS_DIR
        or parts[1] == SOURCE_LANG
        or not is_language_code(parts[1])
        or not rel.endswith(".md")
    ):
        raise ToolError(
            "%s: a translation must be a .md file in docs/<lang>/ (not in docs/en/)" % rel
        )
    for handle in reviewers:
        if not valid_handle(handle):
            raise ToolError("%r is not a GitHub handle" % handle)

    path = root / rel
    text = read_text(path)
    newline = _newline_of(text)
    lines = text.splitlines(keepends=True)
    block = find_header(lines)
    old: Dict[str, object] = dict(block.fields) if block else {}

    if source is None:
        old_source = str(old.get("source") or "")
        source = old_source or expected_source(rel) or ""
    if source.startswith("./"):
        source = source[2:]
    messages: List[str] = []

    if source == NO_SOURCE:
        new_hash = None
    else:
        if source not in english_sources(root):
            raise ToolError(
                "%s: %s is not an English source. Use --source PATH, or --source none for a "
                "file that is not a translation (for example a glossary)." % (rel, source or "(none)")
            )
        new_hash = source_hash(root / source)

    old_status = old.get("status") if old.get("status") in STATUSES else None
    if status:
        new_status = status
    elif old_status == "reviewed" and new_hash is not None and old.get("source_hash") != new_hash:
        new_status = "draft"
        messages.append(
            "%s: the English source changed, so the status changed from reviewed to draft. "
            "After a native review, stamp the file with --status reviewed." % rel
        )
    else:
        new_status = str(old_status or "draft")

    old_with = old.get("translated_with")
    if translated_with:
        new_with: Optional[str] = translated_with
    elif old_with in TRANSLATED_WITH:
        new_with = str(old_with)
    else:
        new_with = None if source == NO_SOURCE else "ai"

    old_reviewers = old.get("reviewed_by")
    kept = [h for h in old_reviewers if valid_handle(str(h))] if isinstance(old_reviewers, list) else []
    header = Header(
        source=source,
        source_hash=new_hash,
        status=new_status,
        translated_with=new_with,
        reviewed_by=_merge_handles(kept, reviewers),
    )
    new_text = with_header(lines, block, header, newline)
    if new_text != text:
        write_text(path, new_text)
        detail = "source: %s" % source if new_hash is None else "source_hash: %s" % new_hash
        messages.insert(0, "%s: stamped (%s, status: %s)" % (rel, detail, new_status))
    else:
        messages.insert(0, "%s: no change" % rel)
    if new_status == "reviewed" and not header.reviewed_by:
        messages.append("%s: warning: the status is reviewed, but reviewed_by is empty. Use --reviewer @handle." % rel)
    return messages


def scaffold_language(root: Path, code: str) -> List[str]:
    """Make docs/<code>/ with a draft copy of each English source."""
    root = Path(root)
    if not is_language_code(code):
        raise ToolError("%r is not a language code. Use a BCP 47 code, for example de or pt-BR." % code)
    if code == SOURCE_LANG:
        raise ToolError("en is the source language. Select a different language.")
    folder = root / DOCS_DIR / code
    if folder.exists():
        raise ToolError("%s/%s/ already exists" % (DOCS_DIR, code))
    sources = english_sources(root)
    if not sources:
        raise ToolError("there are no English sources (README.md or docs/en/*.md)")
    created: List[str] = []
    for source in sources:
        text = read_text(root / source)
        if source == SOURCE_README:
            text = rebase_readme_links(text, sources)
        header = Header(source, source_hash(root / source), "draft", "ai", [])
        lines = text.splitlines(keepends=True)
        dest_rel = translation_path(source, code)
        dest = root / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        write_text(dest, with_header(lines, None, header, _newline_of(text)))
        created.append(dest_rel)
    return created


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--root",
        type=Path,
        default=argparse.SUPPRESS,
        help="the repository root (default: the parent folder of tools/)",
    )
    parser = argparse.ArgumentParser(
        prog="i18n_status.py",
        description="Track the freshness of the documentation translations.",
        parents=[common],
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    sub.required = True

    check = sub.add_parser("check", parents=[common], help="show the status of each translation")
    check.add_argument("--strict", action="store_true", help="exit with code 1 if a file is invalid")
    output = check.add_mutually_exclusive_group()
    output.add_argument(
        "--github-summary", action="store_true", help="print Markdown for $GITHUB_STEP_SUMMARY"
    )
    output.add_argument(
        "--list-outdated",
        action="store_true",
        help="print the outdated, missing, and untranslated files as tab-separated lines: "
        "FRESHNESS LANG TRANSLATION SOURCE",
    )

    stamp = sub.add_parser("stamp", parents=[common], help="write or refresh the i18n header")
    stamp.add_argument("files", nargs="+", metavar="FILE", help="translation files in docs/<lang>/")
    stamp.add_argument("--status", choices=STATUSES, help="set the status")
    stamp.add_argument(
        "--reviewer",
        action="append",
        default=[],
        dest="reviewers",
        metavar="@HANDLE",
        help="add a reviewer (repeat the option, or separate handles with commas)",
    )
    stamp.add_argument("--translated-with", choices=TRANSLATED_WITH, help="set translated_with")
    stamp.add_argument(
        "--source",
        metavar="PATH",
        help="set the English source, or 'none' for a file that is not a translation",
    )

    sub.add_parser("table", parents=[common], help="regenerate the status table in docs/LANGUAGES.md")

    new = sub.add_parser("new", parents=[common], help="make docs/LANG/ with English copies to translate")
    new.add_argument("lang", metavar="LANG", help="BCP 47 language code, for example de or pt-BR")
    return parser


def _use_utf8_output() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass


def main(argv: Optional[Sequence[str]] = None) -> int:
    _use_utf8_output()
    args = build_parser().parse_args(argv)
    root = Path(getattr(args, "root", None) or default_root())
    try:
        if not root.is_dir():
            raise ToolError("%s is not a folder" % root)

        if args.command == "check":
            report = collect(root)
            if args.list_outdated:
                sys.stdout.write(format_list_outdated(report))
            elif args.github_summary:
                sys.stdout.write(format_github_summary(report))
            else:
                sys.stdout.write(format_check(report))
            if args.strict and report.has_invalid():
                print("error: one or more translation files are invalid", file=sys.stderr)
                return 1
            return 0

        if args.command == "stamp":
            reviewers = [h for item in args.reviewers for h in item.split(",") if h.strip()]
            for file_arg in args.files:
                for message in stamp_file(
                    root,
                    file_arg,
                    status=args.status,
                    reviewers=reviewers,
                    translated_with=args.translated_with,
                    source=args.source,
                ):
                    print(message)
            return 0

        if args.command == "table":
            changed = update_languages_table(root)
            print("%s: %s" % (LANGUAGES_FILE, "updated" if changed else "no change"))
            return 0

        if args.command == "new":
            created = scaffold_language(root, args.lang)
            for path in created:
                print("created %s" % path)
            code = args.lang
            print()
            print("Next steps:")
            print("  1. Translate each file in docs/%s/. Keep the i18n header." % code)
            print("  2. Add the label lang:%s to .github/labels.yml and .github/labeler.yml." % code)
            print("  3. Add /docs/%s/ with the reviewers to .github/CODEOWNERS." % code)
            print("  4. Add the reviewers to docs/LANGUAGES.md.")
            print("  5. Run: python3 tools/i18n_status.py table")
            return 0
    except ToolError as error:
        print("error: %s" % error, file=sys.stderr)
        return 1
    return 2  # pragma: no cover


if __name__ == "__main__":
    sys.exit(main())
