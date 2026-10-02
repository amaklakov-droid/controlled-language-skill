# Levels

**English** · [Русский](../ru/levels.md)

The skill has three levels. Each level applies a different set of rules with
a different strength. Level 1 makes the structure of the text clear. Level 2
makes the structure strict. Level 3 applies all rules. In English, Level 3
also controls the vocabulary.

The summary and the level descriptions below are for English, the native
language of the approach. For other languages, see
[Levels in other languages](#levels-in-other-languages).

## Contents

- [Summary](#summary)
- [How the levels work](#how-the-levels-work)
- [Level 1: Light](#level-1-light)
- [Level 2: Standard](#level-2-standard)
- [Level 3: Strict](#level-3-strict)
- [Levels in other languages](#levels-in-other-languages)
- [Select a level](#select-a-level)
- [Which level to use](#which-level-to-use)

## Summary

| | Level 1: Light | Level 2: Standard | Level 3: Strict |
| --- | --- | --- | --- |
| "Must" rules | 19 of 39 (about 50%) | 34 of 39 (about 85%) | 39 of 39 |
| Instruction sentence | max 25 words | max 20 words | max 20 words |
| Description sentence | max 30 words | max 25 words | max 25 words |
| Paragraph | max 8 sentences | max 6 sentences | max 6 sentences |
| Noun cluster | max 4 words | max 3 words | max 3 words |
| Vocabulary | Free, but literal and specific | Simple common words, one meaning for each word | Only approved general words and project terms |
| Phrasal verbs ("set up") | Acceptable | No | No |
| "should", "may", "might" | Acceptable | No | No |
| Verb forms | All | Simple forms preferred | Simple forms only |
| "-ing" forms | Acceptable | Avoid when ambiguous | No (except terms) |
| Spelling | Consistent | Consistent | American |

## How the levels work

The skill has a catalog of 39 rules. Each rule has a strength for each
level:

- **must**: the skill applies the rule every time. A break is a violation.
- **prefer**: the skill applies the rule when it does not make the text less
  clear. A break is a suggestion.
- **off**: the skill does not apply the rule.

The percentages show the share of "must" rules. They are approximate. The
full matrix is in
[rules.md](../../controlled-language/references/rules.md#rule-matrix).

## Level 1: Light

Level 1 makes the structure clear and keeps the voice of the author. Use it
when you want better text with few changes.

At Level 1, the skill:

- writes instructions as imperative, numbered steps;
- puts each condition before its instruction;
- uses the active voice in instructions;
- keeps sentences shorter than 25 words (instructions) and 30 words
  (descriptions);
- removes idioms, metaphors, jokes, and vague words;
- uses one term for each concept;
- writes warnings with a command and a risk.

At Level 1, the skill accepts phrasal verbs, all verb forms, "-ing" forms,
and two related actions in one step.

## Level 2: Standard

Level 2 is the default. It applies all rules for structure and most rules
for words. It is similar to the "80% of the way to ASD-STE100" approach.

At Level 2, the skill also:

- gives one instruction in each sentence;
- keeps sentences shorter than 20 words (instructions) and 25 words
  (descriptions);
- uses simple common words, and one meaning for each word;
- replaces phrasal verbs with one-word verbs ("set up" becomes "configure");
- uses "must", "can", and "do not" instead of "should", "may", "might",
  "could", and "would";
- uses the passive voice in descriptions only when the agent is not
  important;
- does not use semicolons, and does not remove articles.

At Level 2, the skill prefers words that ASD-STE100 approves. Other common
words are acceptable if they have only one meaning in the sentence.

## Level 3: Strict

Level 3 applies all rules. Use it for safety-critical procedures, regulated
products, and text for translation into many languages.

At Level 3, the skill also does these things in English:

- uses only the general words that ASD-STE100 approves, in their approved
  meaning and part of speech;
- uses project terms (technical nouns and technical verbs) for all other
  words;
- uses only simple verb forms: imperative, infinitive, simple present,
  simple past, simple future, and the past participle as an adjective;
- does not use "-ing" forms, except in terms;
- uses the passive voice only when the agent is unknown;
- uses American spelling.

**About the vocabulary.** The ASD-STE100 dictionary belongs to ASD
(Aerospace, Security and Defence Industries Association of Europe). This
project does not contain it. At Level 3, the skill uses the knowledge of the
model about the approved words. When the skill is not sure that a word is
approved, it uses a simpler word. If no simpler word is correct, it lists
the word under "Words to verify". For formal compliance, examine the text
against the [official standard](https://www.asd-ste100.org/).

## Levels in other languages

All three levels work in all languages. The catalog has 39 rules:

- **32 universal rules** apply to all languages, with the same strength at
  each level as in English.
- **7 rules** apply only to English. They control English grammar and the
  ASD-STE100 vocabulary. Examples are the approved words, "-ing" forms,
  phrasal verbs, simple verb forms, and articles.
- **Language rules** apply the universal rules to the grammar of each
  language. For example, the Russian rules (`RU1`–`RU9`) remove verbal
  nouns, bureaucratic words, and adverbial-participle clauses.

| Level | English | Other languages |
| --- | --- | --- |
| 1 Light | 19 "must" rules | Universal rules and language rules at Level 1 strength |
| 2 Standard | 34 "must" rules | Universal rules and language rules at Level 2 strength |
| 3 Strict | All 39 rules and the approved vocabulary | All universal rules and all language rules are "must". No vocabulary control. |

ASD-STE100 has no dictionary for other languages. Thus, Level 3 in other
languages does not control the vocabulary. The skill tells you this when it
applies Level 3 to text that is not in English.

Language files exist for Russian, German, French, and Spanish. They are in
[`controlled-language/references/languages/`](../../controlled-language/references/languages/).
For other languages, the skill uses the universal rules and the usual
conventions of technical writing in that language.

## Select a level

The skill uses the first level that it finds in this order:

1. **The request**: "Level 3", "strict", "light", "80% of the way to
   ASD-STE100".
2. **The front matter** of the document: `controlled-language: 3`.
3. **A path override** in `.controlled-language.yml`.
4. **The default level** in `.controlled-language.yml`.
5. **Level 2**.

You can also change the level for a part of a document with a marker:
`<!-- controlled-language: level 3 -->`. See
[configuration.md](configuration.md).

## Which level to use

| Text | Level |
| --- | --- |
| Internal notes, a draft, a first cleanup of old documentation | 1 |
| Emails, messages, chat answers | 1 or 2 |
| Blog posts and tutorials with a personal style | 1 |
| Reports, policies, explanations, answers of AI agents | 2 |
| User guides, help centers, READMEs, API references | 2 |
| UI text, error messages, release notes | 2 |
| Installation, upgrade, and recovery procedures | 2 or 3 |
| Safety instructions, operations that you cannot reverse, financial operations | 3 |
| Regulated products (medical, aviation, industrial) | 3 |
| Text for machine translation into many languages | 3 |

You can use different levels in one project. For example, set Level 2 as
the default, and set Level 3 for `docs/safety/**` with a path override.
