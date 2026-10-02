# Examples

These examples are real outputs of the skill. We made them during the
evaluation of version 1.0.0. Each folder has the input and the result.

| Folder | Mode and level | What it shows |
| --- | --- | --- |
| [cli-getting-started](cli-getting-started/) | Rewrite, Level 2 | A README section with commands, a YAML file, and UI labels. The code is unchanged. The risk of `direction: mirror` moved from a note to a WARNING before the steps. |
| [webhook-secret-rotation](webhook-secret-rotation/) | Write, Level 3 | A procedure from a list of facts. The skill did not add steps that the facts do not give. It asked questions instead. |
| [russian-2fa](russian-2fa/) | Rewrite, Level 2, Russian | A Russian instruction. The skill applied the universal rules and the Russian rules: it removed verbal nouns and made numbered steps. |
| [russian-backup-level3](russian-backup-level3/) | Rewrite, Level 3, Russian | A Russian guide for administrators at the strict level. The skill kept the command and the paths, added a signal word before the restore command, and did not add steps that the source does not give. |

## Notes from the skill

The skill gives short notes after each document. These are the notes for
the examples.

**cli-getting-started (Level 2)**

- Level 2, from the request ("80% of the way").
- Questions: "every few seconds" is vague. The skill kept the original
  value and asked for the real upload interval.

**webhook-secret-rotation (Level 3)**

- Level 3, from the request.
- Glossary candidates: Payhub, webhook, webhook endpoint, signing secret,
  payment notification, environment variable (nouns). Rotate, sign, verify,
  deploy, click, copy (verbs).
- Words to verify: "reject" and "period".
- Questions: where Payhub shows the new signing secret, and what **Revert**
  does to the new signing secret.

**russian-2fa (Level 2, Russian)**

- Level 2. The universal rules and the Russian rules (`ru.md`). The
  ASD-STE100 vocabulary rules apply only to English.
- Questions: the exact name of the code field, where the service shows the
  backup codes, and which authenticator apps work.

**russian-backup-level3 (Level 3, Russian)**

- Level 3, from the request. The universal rules and the Russian rules are
  "must". There is no vocabulary control for Russian.
- The checker found 13 violations in the original and 0 in the result.
- Questions: the time of minimum load, how to identify the correct backup
  file, and where to run `restore.sh`.

## Check the examples

The checker finds 20 violations in `cli-getting-started/before.md` (182 for
each 100 sentences). It finds 0 violations in `level-2.md`. Run the checker
on a "before" file and on its result:

```bash
python3 controlled-language/scripts/check.py --level 2 examples/cli-getting-started/before.md
python3 controlled-language/scripts/check.py --level 2 examples/cli-getting-started/level-2.md
```
