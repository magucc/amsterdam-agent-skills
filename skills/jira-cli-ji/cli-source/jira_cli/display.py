from typing import Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


# --- ADF text extraction ---

def extract_adf_text(node: Any, depth: int = 0) -> str:
    """Recursively extract plain text from an ADF document node."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if not isinstance(node, dict):
        return ""

    node_type = node.get("type", "")
    text = node.get("text", "")

    if text:
        # Handle marks (bold, code, etc.) — just return text
        return text

    content = node.get("content", [])
    parts = [extract_adf_text(child, depth + 1) for child in content]

    joined = "".join(parts)

    # Add spacing for block-level nodes
    if node_type in ("paragraph", "heading", "listItem", "blockquote"):
        return joined.strip() + "\n"
    if node_type in ("bulletList", "orderedList"):
        return joined
    if node_type == "hardBreak":
        return "\n"
    if node_type == "codeBlock":
        return f"\n{joined.strip()}\n"
    if node_type == "rule":
        return "\n---\n"

    return joined


def render_description(description: Any) -> str:
    if description is None:
        return "(no description)"
    if isinstance(description, str):
        return description or "(no description)"
    text = extract_adf_text(description).strip()
    return text or "(no description)"


# --- Single issue panel ---

def print_issue(issue: dict) -> None:
    fields = issue.get("fields", {})
    key = issue.get("key", "")

    summary = fields.get("summary", "")
    status = fields.get("status", {}).get("name", "Unknown")
    priority = fields.get("priority", {}) or {}
    priority_name = priority.get("name", "None")
    assignee = fields.get("assignee") or {}
    assignee_name = assignee.get("displayName", "Unassigned")
    reporter = fields.get("reporter") or {}
    reporter_name = reporter.get("displayName", "Unknown")
    issue_type = fields.get("issuetype", {}).get("name", "Unknown")
    created = (fields.get("created") or "")[:10]
    updated = (fields.get("updated") or "")[:10]

    description = render_description(fields.get("description"))

    # Build header grid
    meta = Table.grid(padding=(0, 2))
    meta.add_column(style="bold dim")
    meta.add_column()
    meta.add_row("Type", issue_type)
    meta.add_row("Status", _status_text(status))
    meta.add_row("Priority", priority_name)
    meta.add_row("Assignee", assignee_name)
    meta.add_row("Reporter", reporter_name)
    meta.add_row("Created", created)
    meta.add_row("Updated", updated)

    console.print()
    console.print(Panel(
        meta,
        title=f"[bold cyan]{key}[/] [bold]{summary}[/]",
        border_style="cyan",
    ))

    if description and description != "(no description)":
        console.print(Panel(
            description,
            title="Description",
            border_style="dim",
        ))

    # Comments
    comment_data = fields.get("comment", {})
    comments = comment_data.get("comments", []) if isinstance(comment_data, dict) else []
    if comments:
        console.print(f"\n[bold]Comments ({len(comments)})[/]")
        for c in comments:
            author = (c.get("author") or {}).get("displayName", "Unknown")
            created = (c.get("created") or "")[:10]
            body_text = render_description(c.get("body"))
            console.print(Panel(
                body_text,
                title=f"[dim]{author} · {created}[/]",
                border_style="dim",
                padding=(0, 1),
            ))


# --- Issue list table ---

def print_issue_table(issues: list[dict], title: str = "Issues") -> None:
    if not issues:
        console.print(f"[dim]No issues found.[/]")
        return

    table = Table(
        title=title,
        box=box.SIMPLE_HEAD,
        show_lines=False,
        header_style="bold",
    )
    table.add_column("Key", style="cyan bold", no_wrap=True)
    table.add_column("Type", no_wrap=True)
    table.add_column("Status", no_wrap=True)
    table.add_column("Priority", no_wrap=True)
    table.add_column("Assignee")
    table.add_column("Summary")

    for issue in issues:
        fields = issue.get("fields", {})
        key = issue.get("key", "")
        summary = fields.get("summary", "")
        status = fields.get("status", {}).get("name", "")
        priority = (fields.get("priority") or {}).get("name", "")
        assignee = (fields.get("assignee") or {}).get("displayName", "Unassigned")
        issue_type = fields.get("issuetype", {}).get("name", "")

        table.add_row(
            key,
            issue_type,
            _status_text(status),
            priority,
            assignee,
            summary,
        )

    console.print(table)


# --- Transitions table ---

def print_transitions(transitions: list[dict], issue_key: str) -> None:
    if not transitions:
        console.print("[dim]No transitions available.[/]")
        return

    table = Table(
        title=f"Available transitions for {issue_key}",
        box=box.SIMPLE_HEAD,
        header_style="bold",
    )
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name")
    table.add_column("To Status")

    for t in transitions:
        to_status = t.get("to", {}).get("name", "")
        table.add_row(t["id"], t["name"], _status_text(to_status))

    console.print(table)


# --- Projects table ---

def print_projects_table(projects: list[dict]) -> None:
    if not projects:
        console.print("[dim]No projects found.[/]")
        return

    table = Table(
        title=f"Projects ({len(projects)})",
        box=box.SIMPLE_HEAD,
        header_style="bold",
    )
    table.add_column("Key", style="cyan bold", no_wrap=True)
    table.add_column("Name")
    table.add_column("Type", no_wrap=True)
    table.add_column("Lead")

    for p in projects:
        lead = (p.get("lead") or {}).get("displayName", "")
        table.add_row(
            p.get("key", ""),
            p.get("name", ""),
            p.get("projectTypeKey", ""),
            lead,
        )

    console.print(table)


# --- Helpers ---

STATUS_COLORS = {
    "to do": "white",
    "in progress": "yellow",
    "done": "green",
    "closed": "green",
    "blocked": "red",
    "in review": "blue",
    "backlog": "dim",
}


def _status_text(status: str) -> str:
    color = STATUS_COLORS.get(status.lower(), "white")
    return f"[{color}]{status}[/]"


def print_error(message: str) -> None:
    console.print(f"[bold red]Error:[/] {message}")


def print_success(message: str) -> None:
    console.print(f"[bold green]✓[/] {message}")
