# Innovation Agent Skills

Open-source agent skills by the Innovation team at the Municipality of Amsterdam. Skills are knowledge modules that give AI coding assistants context-aware expertise — automatically activated when relevant to the task at hand.

Compatible with tools that support skill/instruction files, including Claude Code, GitHub Copilot, Cursor, and others.

## Quick Install

Install skills with [`npx skills`](https://github.com/vercel-labs/skills):

```bash
# Install all skills from this repo
npx skills add amsterdam/innovation-agent-skills

# Install a specific skill
npx skills add amsterdam/innovation-agent-skills --skill amsterdam-design-system

# Install for a specific agent
npx skills add amsterdam/innovation-agent-skills -a claude-code
npx skills add amsterdam/innovation-agent-skills -a cursor

# Preview available skills without installing
npx skills add amsterdam/innovation-agent-skills --list
```

## Manual Setup

Each skill lives in `skills/<name>/SKILL.md`. How you load them depends on your tool:

| Tool | Setup |
|------|-------|
| Claude Code | Symlink into `~/.claude/skills/` |
| GitHub Copilot | Reference in `.github/copilot-instructions.md` |
| Cursor | Add to `.cursor/rules/` |

**Claude Code example:**

```bash
for skill in skills/*/; do
  ln -sf "$(pwd)/$skill" ~/.claude/skills/$(basename "$skill")
done
```

## Skills

| Skill | Description |
|-------|-------------|
| [amsterdam-design-system](skills/amsterdam-design-system/) | Gemeente Amsterdam design system — React components, `--ams-*` tokens, Grid layout, Spacious/Compact modes, Tailwind v4 bridge |
| [amsterdam-stijl](skills/amsterdam-stijl/) | Amsterdam municipality writing style — Heldere Taal (B1), Eenvoudige Taal (A2), inclusive language, tone of voice, word choice, text templates |
| [jira-cli-ji](skills/jira-cli-ji/) | Jira CLI (ji) — PAT-based issue tracking, sprint management, JQL search, workflow automation |

## Structure

```
skills/
├── amsterdam-design-system/    # AMS React + tokens + layout
│   ├── SKILL.md
│   └── references/             # Component APIs, token catalog, templates
├── amsterdam-stijl/            # Writing style, tone, language guidelines
│   ├── SKILL.md
│   └── references/             # Word lists, examples, templates
├── jira-cli-ji/                # Jira CLI (PAT auth, no OAuth)
│   ├── SKILL.md
│   ├── cli-source/             # Python CLI package
│   └── references/
└── [new-skill]/
    └── SKILL.md                # Single-file skills
```

## Adding a New Skill

1. Create `skills/my-skill/SKILL.md` with a clear description and instructions
2. Add reference files in `skills/my-skill/references/` if needed
3. Update this README table
