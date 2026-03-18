# JQL Patterns Reference

Quick reference for Jira Query Language (JQL) used with `ji search "<jql>"`.

## Operators

| Operator | Example | Notes |
|----------|---------|-------|
| `=` | `status = "In Progress"` | Exact match (quote values with spaces) |
| `!=` | `status != Done` | Not equal |
| `IN` | `status IN ("To Do", "In Progress")` | Match any in list |
| `NOT IN` | `priority NOT IN (Low, Lowest)` | Exclude list |
| `~` | `summary ~ "auth"` | Contains text (fields: summary, description, comment) |
| `!~` | `summary !~ "test"` | Does not contain |
| `IS` | `assignee IS EMPTY` | Null check |
| `IS NOT` | `assignee IS NOT EMPTY` | Not null |
| `>`, `>=`, `<`, `<=` | `created >= -7d` | Comparison (dates, priority) |
| `WAS` | `status WAS "In Progress"` | Historical value |
| `CHANGED` | `status CHANGED` | Field was modified |

## Functions

| Function | Usage | Description |
|----------|-------|-------------|
| `currentUser()` | `assignee = currentUser()` | The authenticated user |
| `openSprints()` | `sprint IN openSprints()` | Active sprints |
| `closedSprints()` | `sprint IN closedSprints()` | Completed sprints |
| `futureSprints()` | `sprint IN futureSprints()` | Upcoming sprints |
| `now()` | `due <= now()` | Current timestamp |
| `startOfDay()` | `created >= startOfDay()` | Start of today |
| `startOfWeek()` | `created >= startOfWeek()` | Start of this week |
| `startOfMonth()` | `created >= startOfMonth()` | Start of this month |
| `endOfDay()` | `due <= endOfDay()` | End of today |
| `endOfWeek()` | `due <= endOfWeek()` | End of this week |
| `membersOf()` | `assignee IN membersOf("team-name")` | Group members |

## Relative Dates

Use with `created`, `updated`, `due`, `resolved`:

| Pattern | Meaning |
|---------|---------|
| `-1d` | 1 day ago |
| `-7d` | 7 days ago |
| `-2w` | 2 weeks ago |
| `-1M` | 1 month ago |
| `"2026-03-01"` | Specific date (YYYY-MM-DD) |

## Common Queries

### By Sprint

```jql
# Current sprint issues
project = PROJ AND sprint IN openSprints()

# Current sprint, not done
project = PROJ AND sprint IN openSprints() AND statusCategory != Done

# Unfinished from last sprint (spillover)
project = PROJ AND sprint IN closedSprints() AND statusCategory != Done
```

### By Assignee

```jql
# My open issues
assignee = currentUser() AND statusCategory != Done

# Unassigned in current sprint
project = PROJ AND sprint IN openSprints() AND assignee IS EMPTY

# Someone else's issues
assignee = "user@example.com" AND statusCategory != Done
```

### By Status

```jql
# Blocked issues
project = PROJ AND status = "Blocked"

# In progress across all projects
status = "In Progress" AND assignee = currentUser()

# Items in review
project = PROJ AND status = "In Review"
```

### By Type

```jql
# All bugs in project
project = PROJ AND issuetype = Bug

# Open bugs, high priority
project = PROJ AND issuetype = Bug AND priority IN (High, Highest) AND statusCategory != Done

# Epics
project = PROJ AND issuetype = Epic
```

### By Labels

```jql
# Issues with specific label
project = PROJ AND labels = "tech-debt"

# Issues with any of several labels
project = PROJ AND labels IN ("frontend", "backend")

# Unlabeled issues
project = PROJ AND labels IS EMPTY
```

### By Dates

```jql
# Created this week
project = PROJ AND created >= startOfWeek()

# Updated in last 24 hours
project = PROJ AND updated >= -1d

# Overdue issues
project = PROJ AND due < now() AND statusCategory != Done

# Due this week
project = PROJ AND due >= startOfWeek() AND due <= endOfWeek()
```

### By Text

```jql
# Search summary
summary ~ "authentication"

# Search summary and description
text ~ "login error"

# Issues with comments mentioning something
comment ~ "deployed"
```

## Ordering

Append `ORDER BY` to any query:

```jql
# By priority (highest first)
... ORDER BY priority ASC

# By most recently updated
... ORDER BY updated DESC

# By creation date
... ORDER BY created DESC

# Multiple sort keys
... ORDER BY priority ASC, updated DESC
```

Note: `ji list` appends `ORDER BY updated DESC` automatically. `ji search` uses your JQL as-is — add your own `ORDER BY`.

## Combined Examples

### Standup prep — what changed overnight

```jql
project = PROJ AND updated >= -16h AND sprint IN openSprints() ORDER BY updated DESC
```

### Triage — new unassigned bugs

```jql
project = PROJ AND issuetype = Bug AND assignee IS EMPTY AND created >= -7d ORDER BY priority ASC, created DESC
```

### Sprint review — completed this sprint

```jql
project = PROJ AND sprint IN openSprints() AND statusCategory = Done ORDER BY resolved DESC
```

### Tech debt sweep

```jql
project = PROJ AND labels = "tech-debt" AND statusCategory != Done ORDER BY priority ASC
```

### Cross-project search

```jql
assignee = currentUser() AND statusCategory != Done ORDER BY project ASC, priority ASC
```

### Stale issues — no updates in 30 days

```jql
project = PROJ AND statusCategory != Done AND updated <= -30d ORDER BY updated ASC
```

### Recently resolved by me

```jql
assignee = currentUser() AND statusCategory = Done AND resolved >= -7d ORDER BY resolved DESC
```
