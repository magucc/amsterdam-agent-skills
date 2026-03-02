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

## Structure

```
skills/
├── amsterdam-design-system/    # AMS React + tokens + layout
│   ├── SKILL.md
│   └── references/             # Component APIs, token catalog, templates
└── [new-skill]/
    └── SKILL.md                # Single-file skills
```

## Adding a New Skill

1. Create `skills/my-skill/SKILL.md` with a clear description and instructions
2. Add reference files in `skills/my-skill/references/` if needed
3. Update this README table
