# Installation

**English** · [Русский](../ru/installation.md)

The skill is a folder: `controlled-language/`. The folder contains `SKILL.md`
and its reference files. It follows the open
[Agent Skills](https://agentskills.io) standard, so the same folder works in
each agent that supports `SKILL.md`.

Select your agent:

- [Any agent: the `skills` installer](#any-agent-the-skills-installer)
- [Claude Code](#claude-code)
- [Claude.ai and Claude Desktop](#claudeai-and-claude-desktop)
- [Claude API and Claude Agent SDK](#claude-api-and-claude-agent-sdk)
- [OpenAI Codex, GitHub Copilot, Cursor, Gemini CLI, and other agents](#openai-codex-github-copilot-cursor-gemini-cli-and-other-agents)
- [Chat models without skill support](#chat-models-without-skill-support)

After the installation, do the [test](#test-the-installation).

## Any agent: the `skills` installer

The [`skills` CLI](https://github.com/vercel-labs/skills) installs the skill
into the agents that you select. You need Node.js 18 or later.

```bash
npx skills add amaklakov-droid/controlled-language-skill
```

The installer asks which agents to use. To install the skill for all your
projects and for one agent (for example, Codex), use these options:

```bash
npx skills add amaklakov-droid/controlled-language-skill -g -a codex
```

## Claude Code

### As a plugin

Add the repository as a plugin marketplace. Then install the plugin. Type
these commands in Claude Code:

```
/plugin marketplace add amaklakov-droid/controlled-language-skill
/plugin install controlled-language@controlled-language-skill
```

To get updates, type `/plugin marketplace update controlled-language-skill`.

### As a folder

1. Clone the repository:

   ```bash
   git clone https://github.com/amaklakov-droid/controlled-language-skill.git
   ```

2. Copy the skill folder into your personal skills folder:

   ```bash
   mkdir -p ~/.claude/skills
   rm -rf ~/.claude/skills/controlled-language
   cp -R controlled-language-skill/controlled-language ~/.claude/skills/controlled-language
   ```

   To use the skill in one project only, copy the folder into
   `<project>/.claude/skills/` instead.

> Note: write the destination folder name in full, as the command above
> shows. On macOS, if the source path ends with `/`, `cp` copies only the
> contents of the folder.

You can start the skill directly: `/controlled-language rewrite README.md at
Level 3`.

## Claude.ai and Claude Desktop

1. Make a ZIP file of the `controlled-language/` folder. `SKILL.md` must be at
   the top of the folder in the ZIP file.

   ```bash
   cd controlled-language-skill
   zip -r controlled-language.zip controlled-language
   ```

2. Open **Settings → Capabilities → Skills**.
3. Click **Upload skill** and select `controlled-language.zip`.

The checker script needs code execution. If code execution is off, the skill
works without the checker.

## Claude API and Claude Agent SDK

- **Claude API**: upload the `controlled-language/` folder with the
  [Skills API](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview).
  Then add the skill to the container of your request.
- **Claude Agent SDK**: copy the folder into `.claude/skills/` of the working
  directory of the agent. Then enable the skills setting of the SDK.

## OpenAI Codex, GitHub Copilot, Cursor, Gemini CLI, and other agents

These agents read skills from the shared project folder `.agents/skills/`.
Each agent also has its own global folder.

**One project.** Copy the skill folder into `.agents/skills/` of your
project:

```bash
mkdir -p .agents/skills
cp -R controlled-language-skill/controlled-language .agents/skills/controlled-language
```

**All your projects.** Copy the skill folder into the global folder of your
agent:

| Agent | Global folder |
| --- | --- |
| OpenAI Codex | `~/.codex/skills/` |
| GitHub Copilot | `~/.copilot/skills/` |
| Cursor | `~/.cursor/skills/` |
| Gemini CLI | `~/.gemini/skills/` |
| OpenCode | `~/.config/opencode/skills/` |
| Goose | `~/.config/goose/skills/` |

For example, for Codex:

```bash
mkdir -p ~/.codex/skills
cp -R controlled-language-skill/controlled-language ~/.codex/skills/controlled-language
```

Some agents also read their own project folders, for example
`.github/skills/` (GitHub Copilot). If your agent is not in the list, read
its documentation. Look for "Agent Skills" or "SKILL.md". The `skills`
installer knows the folders of many agents.

## Chat models without skill support

ChatGPT, Gemini, DeepSeek, Mistral, and local models do not read `SKILL.md`
files. Use the one-file version of the skill:

1. Open [prompts/system-prompt.md](../../prompts/system-prompt.md).
2. Copy the text between the two lines `--- BEGIN PROMPT ---` and
   `--- END PROMPT ---`.
3. Paste the text into one of these places:
   - **ChatGPT**: a custom GPT (Instructions), a Project (Instructions), or
     **Settings → Personalization → Custom instructions**.
   - **Gemini**: a Gem (Instructions).
   - **API or local model**: the system prompt.
4. Change the line `Default level: 2` if you want a different default level.

For the best results with long documents, also attach
[`references/rules.md`](../../controlled-language/references/rules.md) to the
conversation.

## Test the installation

Start a new session of your agent. Then send this request:

```
Rewrite this text in controlled English, Level 2:
"Once the migration has been completed, you should simply restart the
service in order to apply the changes."
```

A correct answer is similar to this:

> After the migration is complete, restart the service to apply the changes.

The answer also gives the level and its source, for example "Level 2
(request)". If the agent does not use the skill, write "Use the
controlled-language skill" in the request. Then examine the folder location.

## Update and remove

- **`skills` installer**: run `npx skills update controlled-language` to
  update. Run `npx skills remove controlled-language` to remove.
- **Claude Code plugin**: run `/plugin marketplace update
  controlled-language-skill` to update. Run `/plugin uninstall
  controlled-language` to remove.
- **Folder copy**: run `git pull` in the cloned repository and copy the
  folder again. To remove the skill, delete the folder.
