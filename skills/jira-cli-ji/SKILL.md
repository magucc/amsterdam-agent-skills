---
name: jira-cli-ji
description: Jira CLI (ji) — PAT-based issue tracking, sprint management, JQL search, workflow automation for Gemeente Amsterdam
triggers:
  - jira
  - ji
  - sprint
  - issue tracking
  - backlog
  - tickets
  - standup
  - triage
  - PAT
---

# Jira CLI (ji)

`ji` is a lightweight Jira CLI built for Gemeente Amsterdam's Innovation team. It uses **Basic Auth with a Personal Access Token (PAT)** because the org blocks OAuth application registration on Jira. The CLI wraps the Jira REST API v3 with a clean interface for issue tracking, sprint management, and JQL search.

## Setup

### Install

```bash
uv tool install ./skills/jira-cli-ji/cli-source
```

### Configure credentials

**Option A — Doppler (preferred for agent workflows):**

Set these environment variables in your Doppler project:

| Variable | Description |
|----------|-------------|
| `JIRA_ORG_URL` | e.g. `https://myorg.atlassian.net` |
| `JIRA_EMAIL` | Jira account email |
| `JIRA_API_KEY` | API token from [Atlassian API tokens](https://id.atlassian.com/manage-profile/security/api-tokens) |

Then run commands with `doppler run -- ji <command>`.

**Option B — Config file:**

Ask the user to run `ji configure` interactively (this command uses `click.prompt` and cannot be run by the agent). This saves credentials to `~/.jira-cli.json` (chmod 600).

### Auth resolution order

1. CLI flags (`--org-url`, `--email`, `--api-key`)
2. Environment variables (`JIRA_ORG_URL`, `JIRA_EMAIL`, `JIRA_API_KEY`)
3. Config file (`~/.jira-cli.json`)

## Quick Reference

| Command | Description |
|---------|-------------|
| `ji projects` | List all accessible projects |
| `ji list -p PROJ` | List issues in a project |
| `ji list -p PROJ --sprint current` | Current sprint issues |
| `ji list -p PROJ --assignee me` | My issues in project |
| `ji me` | My open issues (all projects or default) |
| `ji view PROJ-123` | View issue details |
| `ji create -p PROJ -s "Summary"` | Create a task |
| `ji create -p PROJ -s "Bug title" -t Bug` | Create a bug |
| `ji update PROJ-123 --status "In Progress"` | Transition status |
| `ji update PROJ-123 --assignee me` | Assign to yourself |
| `ji update PROJ-123 --comment "Note"` | Add a comment |
| `ji update PROJ-123 -l "tech-debt"` | Add a label |
| `ji assign PROJ-123` | Assign to yourself |
| `ji assign PROJ-123 user@example.com` | Assign to someone |
| `ji assign PROJ-123 none` | Unassign |
| `ji comment PROJ-123 "Done"` | Add a comment |
| `ji transitions PROJ-123` | Show available status transitions |
| `ji search "JQL query"` | Raw JQL search |

## Command Details

### `ji projects`

Lists all Jira projects accessible to the authenticated user.

```bash
ji projects
```

### `ji list`

Lists issues in a project with optional filters.

```bash
# All issues in project
ji list -p PROJ

# Current sprint only
ji list -p PROJ --sprint current

# My issues in current sprint
ji list -p PROJ --sprint current --assignee me

# Filter by status
ji list -p PROJ --status "In Progress"

# Limit results
ji list -p PROJ --limit 50
```

If `--project` / `-p` is omitted, uses `default_project` from config.

### `ji me`

Shortcut for "my open issues" — shows all non-Done issues assigned to you.

```bash
# All projects
ji me

# Specific project
ji me -p PROJ

# More results
ji me --limit 50
```

### `ji view`

Shows full issue details: type, status, priority, assignee, reporter, dates, description, and comments.

```bash
ji view PROJ-123
```

Output is a Rich panel — not JSON. For structured data, use the Jira API directly.

### `ji create`

Creates a new issue. Summary is required.

```bash
# Basic task
ji create -p PROJ -s "Implement auth middleware"

# Bug with details
ji create -p PROJ -s "Login fails on Safari" -t Bug -d "Steps to reproduce..." --priority High

# Story with labels, assigned to me
ji create -p PROJ -s "User can reset password" -t Story -l "auth" -l "mvp" --assignee me
```

**Options:**

| Flag | Description |
|------|-------------|
| `-p` / `--project` | Project key (or uses default) |
| `-s` / `--summary` | Issue summary (required) |
| `-t` / `--type` | Issue type: Task (default), Bug, Story, Epic |
| `-d` / `--description` | Description text |
| `-l` / `--label` | Label (repeatable for multiple) |
| `--priority` | High, Medium, Low, etc. |
| `--assignee` | Email or `me` |

### `ji update`

Updates one or more fields on an existing issue. Combine multiple flags in one call.

```bash
# Change status
ji update PROJ-123 --status "In Progress"

# Reassign and comment
ji update PROJ-123 --assignee me --comment "Picking this up"

# Add labels and set priority
ji update PROJ-123 -l "urgent" -l "frontend" --priority High

# Change summary
ji update PROJ-123 --summary "New title for the issue"
```

**Status transitions:** The `--status` flag performs a Jira transition, not a field edit. The target status name must match an available transition. Always check valid transitions first with `ji transitions PROJ-123`.

### `ji assign`

Quick assignment shortcut.

```bash
ji assign PROJ-123            # Assign to yourself
ji assign PROJ-123 user@email # Assign to someone
ji assign PROJ-123 none       # Unassign
```

### `ji comment`

Adds a comment to an issue.

```bash
ji comment PROJ-123 "Deployed to staging, ready for review"
```

### `ji transitions`

Shows available status transitions for an issue. **Always run this before `ji update --status`** — valid transitions vary by project workflow configuration.

```bash
ji transitions PROJ-123
```

### `ji search`

Runs a raw JQL query. You control the full query including `ORDER BY`.

```bash
# Current sprint bugs
ji search "project = PROJ AND issuetype = Bug AND sprint IN openSprints()"

# Overdue items
ji search "project = PROJ AND due < now() AND statusCategory != Done ORDER BY due ASC"

# Cross-project search
ji search "assignee = currentUser() AND statusCategory != Done ORDER BY updated DESC" --limit 50
```

See `references/jql-patterns.md` for comprehensive JQL syntax and patterns.

## Workflow Patterns

### Standup prep

```bash
# What's in my queue
ji me -p PROJ

# What changed overnight in the sprint
ji search "project = PROJ AND updated >= -16h AND sprint IN openSprints() ORDER BY updated DESC"
```

### Pick up work

```bash
# Find unassigned sprint work
ji list -p PROJ --sprint current --assignee me  # Check current load first
ji search "project = PROJ AND sprint IN openSprints() AND assignee IS EMPTY ORDER BY priority ASC"

# Grab an issue
ji assign PROJ-456
ji update PROJ-456 --status "In Progress" --comment "Starting work"
```

### Create and assign

```bash
# Create a bug and assign to yourself
ji create -p PROJ -s "API returns 500 on empty payload" -t Bug --priority High --assignee me -l "api"

# Create a task for someone else
ji create -p PROJ -s "Update API docs" --assignee colleague@amsterdam.nl -l "docs"
```

### Triage new issues

```bash
# Find unassigned bugs from last week
ji search "project = PROJ AND issuetype = Bug AND assignee IS EMPTY AND created >= -7d ORDER BY priority ASC"

# Review and assign each
ji view PROJ-789
ji update PROJ-789 --priority High --assignee dev@amsterdam.nl --comment "Needs fix before release"
```

### Complete and hand off

```bash
# Check valid transitions
ji transitions PROJ-123

# Move to review
ji update PROJ-123 --status "In Review" --comment "PR #42 ready for review"

# Mark done
ji update PROJ-123 --status "Done" --comment "Merged and deployed"
```

### Sprint refinement

```bash
# Check backlog
ji list -p PROJ --status "Backlog" --limit 50

# Review an issue
ji view PROJ-234

# Update for sprint readiness
ji update PROJ-234 --priority Medium -l "sprint-ready" --comment "Refined, estimated at 3 points"
```

## Agent Guidelines

1. **Always check transitions before status change.** Run `ji transitions PROJ-123` before `ji update PROJ-123 --status "..."`. Status names vary per project — never assume.

2. **Use `--limit` on list/search commands.** Default is 20. Don't fetch unbounded result sets.

3. **Never run `ji configure`.** It's interactive (`click.prompt`). If credentials aren't set up, ask the user to either:
   - Run `ji configure` themselves, or
   - Set `JIRA_ORG_URL`, `JIRA_EMAIL`, `JIRA_API_KEY` via Doppler

4. **Output is Rich-formatted, not JSON.** `ji` renders tables and panels for human readability. Don't try to parse the output programmatically — use the information visually.

5. **Label hygiene.** Use lowercase, hyphenated labels (`tech-debt`, `sprint-ready`, `needs-review`). Check existing labels before creating new ones.

6. **Quote JQL values with spaces.** `status = "In Progress"`, not `status = In Progress`.

7. **Use `me` shortcut.** When assigning or filtering by the authenticated user, use `me` instead of an email address.

8. **Batch updates.** Combine flags in a single `ji update` call rather than making multiple calls: `ji update PROJ-123 --status "In Progress" --assignee me --comment "On it" -l "in-sprint"`.

## Do / Don't

| Do | Don't |
|----|-------|
| `ji transitions PROJ-123` before status change | Guess status names — they vary per project |
| Use `--limit` on search/list | Fetch all issues without limits |
| Use `me` for self-assignment | Hard-code email addresses |
| Ask user to run `ji configure` | Run `ji configure` (interactive, will hang) |
| Quote JQL values with spaces | `status = In Progress` (syntax error) |
| Combine flags in one `ji update` | Make 4 separate `ji update` calls |
| Use Doppler for credentials | Put credentials in `.env` files |
| Check existing labels first | Create duplicate/variant labels |
| Use `ji search` for complex queries | Chain multiple `ji list` with grep |

## References

- JQL syntax and patterns: `references/jql-patterns.md`
- CLI source: `cli-source/` (Python, installable with `uv tool install`)
