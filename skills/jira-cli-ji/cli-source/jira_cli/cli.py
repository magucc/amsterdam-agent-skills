import sys

import click

from .client import JiraClient, JiraError
from .config import load_config, resolve_config, save_config, CONFIG_PATH
from .display import (
    console,
    print_error,
    print_issue,
    print_issue_table,
    print_projects_table,
    print_success,
    print_transitions,
)


# ---------------------------------------------------------------------------
# Shared options
# ---------------------------------------------------------------------------

_auth_options = [
    click.option("--org-url", envvar="JIRA_ORG_URL", default=None, help="Jira org URL"),
    click.option("--email", envvar="JIRA_EMAIL", default=None, help="Jira account email"),
    click.option("--api-key", envvar="JIRA_API_KEY", default=None, help="Jira API token"),
]


def add_auth_options(fn):
    for option in reversed(_auth_options):
        fn = option(fn)
    return fn


def make_client(org_url, email, api_key) -> JiraClient:
    try:
        resolved_url, resolved_email, resolved_key = resolve_config(org_url, email, api_key)
    except ValueError as e:
        print_error(str(e))
        sys.exit(1)
    return JiraClient(resolved_url, resolved_email, resolved_key)


def handle_jira_error(fn):
    """Decorator to catch JiraError and exit cleanly."""
    import functools

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except JiraError as e:
            print_error(str(e))
            sys.exit(1)

    return wrapper


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
def cli():
    """Jira CLI — lightweight Jira client using Basic Auth."""
    pass


# ---------------------------------------------------------------------------
# configure
# ---------------------------------------------------------------------------

@cli.command()
def configure():
    """Interactive setup — saves credentials to ~/.jira-cli.json."""
    console.print("[bold]Jira CLI Configuration[/]\n")

    existing = load_config()

    org_url = click.prompt(
        "Jira org URL (e.g. https://myorg.atlassian.net)",
        default=existing.get("org_url", ""),
    )
    email = click.prompt(
        "Account email",
        default=existing.get("email", ""),
    )
    api_key = click.prompt(
        "API token (from https://id.atlassian.com/manage-profile/security/api-tokens)",
        default=existing.get("api_key", ""),
        hide_input=True,
    )
    default_project = click.prompt(
        "Default project key (optional, e.g. SRDO)",
        default=existing.get("default_project", ""),
    )

    save_config(org_url, email, api_key, default_project)
    print_success(f"Config saved to {CONFIG_PATH}")

    # Quick auth check
    console.print("[dim]Verifying credentials…[/]")
    try:
        with JiraClient(org_url, email, api_key) as client:
            me = client.get_myself()
        print_success(f"Authenticated as {me.get('displayName')} ({me.get('emailAddress')})")
    except JiraError as e:
        print_error(f"Auth check failed: {e}")


# ---------------------------------------------------------------------------
# projects
# ---------------------------------------------------------------------------

@cli.command()
@add_auth_options
@handle_jira_error
def projects(org_url, email, api_key):
    """List all projects you have access to."""
    with make_client(org_url, email, api_key) as client:
        data = client.get_projects()
    print_projects_table(data)


# ---------------------------------------------------------------------------
# view
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("issue_key")
@add_auth_options
@handle_jira_error
def view(issue_key, org_url, email, api_key):
    """View details for an issue."""
    with make_client(org_url, email, api_key) as client:
        issue = client.get_issue(issue_key)
    print_issue(issue)


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("issue_key")
@click.option("--status", default=None, help="Transition to this status name")
@click.option("--assignee", default=None, help="Assign to email address ('me' for yourself)")
@click.option("--summary", default=None, help="New summary text")
@click.option("--comment", default=None, help="Add a comment")
@click.option("--priority", default=None, help="Set priority (e.g. High, Medium, Low)")
@click.option("--label", "-l", multiple=True, help="Add label(s) to the issue (repeatable)")
@add_auth_options
@handle_jira_error
def update(issue_key, status, assignee, summary, comment, priority, label, org_url, email, api_key):
    """Update issue fields."""
    with make_client(org_url, email, api_key) as client:
        fields: dict = {}
        update_ops: dict = {}

        if summary:
            fields["summary"] = summary

        if priority:
            fields["priority"] = {"name": priority}

        if assignee:
            if assignee.lower() == "me":
                me = client.get_myself()
                fields["assignee"] = {"accountId": me["accountId"]}
            else:
                user = client.find_user_by_email(assignee)
                if not user:
                    print_error(f"No user found for email: {assignee}")
                    sys.exit(1)
                fields["assignee"] = {"accountId": user["accountId"]}

        if label:
            update_ops["labels"] = [{"add": lb} for lb in label]

        if fields or update_ops:
            client.update_issue(issue_key, fields, update_ops or None)
            print_success(f"Updated {issue_key}")

        if status:
            transitions = client.get_transitions(issue_key)
            match = next(
                (t for t in transitions if t["name"].lower() == status.lower()),
                None,
            )
            if not match:
                available = ", ".join(t["name"] for t in transitions)
                print_error(
                    f"Status '{status}' not available. Available: {available}"
                )
                sys.exit(1)
            client.transition_issue(issue_key, match["id"])
            print_success(f"Transitioned {issue_key} to '{status}'")

        if comment:
            client.add_comment(issue_key, comment)
            print_success(f"Comment added to {issue_key}")

        if not any([fields, update_ops, status, comment]):
            print_error("No update flags provided. Use --help to see options.")
            sys.exit(1)


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

@cli.command(name="list")
@click.option("--project", "-p", default=None, help="Project key (e.g. PROJ). Defaults to config value.")
@click.option("--status", default=None, help="Filter by status name")
@click.option("--assignee", default=None, help="Filter by assignee email ('me' for yourself)")
@click.option("--sprint", default=None, type=click.Choice(["current"]), help="Filter to current sprint")
@click.option("--limit", default=20, show_default=True, help="Max results")
@add_auth_options
@handle_jira_error
def list_issues(project, status, assignee, sprint, limit, org_url, email, api_key):
    """List issues in a project."""
    if not project:
        project = load_config().get("default_project")
    if not project:
        print_error("No project specified. Use -p/--project or set default_project in `ji configure`.")
        sys.exit(1)
    with make_client(org_url, email, api_key) as client:
        clauses = [f"project = {project}"]

        if status:
            clauses.append(f'status = "{status}"')

        if assignee:
            if assignee.lower() == "me":
                clauses.append("assignee = currentUser()")
            else:
                user = client.find_user_by_email(assignee)
                if not user:
                    print_error(f"No user found for email: {assignee}")
                    sys.exit(1)
                clauses.append(f'assignee = "{user["accountId"]}"')

        if sprint == "current":
            clauses.append("sprint in openSprints()")

        jql = " AND ".join(clauses) + " ORDER BY updated DESC"
        result = client.search(
            jql,
            max_results=limit,
            fields=["summary", "status", "assignee", "priority", "issuetype"],
        )

    issues = result.get("issues", [])
    total = result.get("total", 0)
    title = f"[{project}] Issues — {len(issues)} of {total}"
    print_issue_table(issues, title=title)


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("jql")
@click.option("--limit", default=20, show_default=True, help="Max results")
@add_auth_options
@handle_jira_error
def search(jql, limit, org_url, email, api_key):
    """Run a raw JQL search."""
    with make_client(org_url, email, api_key) as client:
        result = client.search(
            jql,
            max_results=limit,
            fields=["summary", "status", "assignee", "priority", "issuetype"],
        )

    issues = result.get("issues", [])
    total = result.get("total", 0)
    title = f"Search results — {len(issues)} of {total}"
    print_issue_table(issues, title=title)


# ---------------------------------------------------------------------------
# comment
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("issue_key")
@click.argument("text")
@add_auth_options
@handle_jira_error
def comment(issue_key, text, org_url, email, api_key):
    """Add a comment to an issue."""
    with make_client(org_url, email, api_key) as client:
        client.add_comment(issue_key, text)
    print_success(f"Comment added to {issue_key}")


# ---------------------------------------------------------------------------
# transitions
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("issue_key")
@add_auth_options
@handle_jira_error
def transitions(issue_key, org_url, email, api_key):
    """Show available status transitions for an issue."""
    with make_client(org_url, email, api_key) as client:
        t = client.get_transitions(issue_key)
    print_transitions(t, issue_key)


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--project", "-p", default=None, help="Project key. Defaults to config value.")
@click.option("--summary", "-s", required=True, help="Issue summary")
@click.option("--type", "-t", "issue_type", default="Task", show_default=True, help="Issue type (Task, Bug, Story, Epic)")
@click.option("--description", "-d", default="", help="Issue description")
@click.option("--label", "-l", multiple=True, help="Label(s) (repeatable)")
@click.option("--priority", default=None, help="Priority (e.g. High, Medium, Low)")
@click.option("--assignee", default=None, help="Assignee email ('me' for yourself)")
@add_auth_options
@handle_jira_error
def create(project, summary, issue_type, description, label, priority, assignee, org_url, email, api_key):
    """Create a new issue."""
    if not project:
        project = load_config().get("default_project")
    if not project:
        print_error("No project specified. Use -p/--project or set default_project in `ji configure`.")
        sys.exit(1)

    with make_client(org_url, email, api_key) as client:
        assignee_id = None
        if assignee:
            if assignee.lower() == "me":
                assignee_id = client.get_myself()["accountId"]
            else:
                user = client.find_user_by_email(assignee)
                if not user:
                    print_error(f"No user found for email: {assignee}")
                    sys.exit(1)
                assignee_id = user["accountId"]

        result = client.create_issue(
            project_key=project,
            summary=summary,
            issue_type=issue_type,
            description=description,
            labels=list(label) or None,
            priority=priority,
            assignee_id=assignee_id,
        )

    key = result.get("key", "")
    print_success(f"Created {key}: {summary}")


# ---------------------------------------------------------------------------
# assign
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("issue_key")
@click.argument("who", default="me")
@add_auth_options
@handle_jira_error
def assign(issue_key, who, org_url, email, api_key):
    """Assign an issue. Defaults to yourself (me)."""
    with make_client(org_url, email, api_key) as client:
        if who.lower() == "me":
            account_id = client.get_myself()["accountId"]
        elif who.lower() == "none":
            client.update_issue(issue_key, {"assignee": None})
            print_success(f"Unassigned {issue_key}")
            return
        else:
            user = client.find_user_by_email(who)
            if not user:
                print_error(f"No user found for: {who}")
                sys.exit(1)
            account_id = user["accountId"]
        client.update_issue(issue_key, {"assignee": {"accountId": account_id}})
    print_success(f"Assigned {issue_key} to {who}")


# ---------------------------------------------------------------------------
# me
# ---------------------------------------------------------------------------

@cli.command()
@click.option("--project", "-p", default=None, help="Filter to project. Defaults to config value.")
@click.option("--limit", default=20, show_default=True, help="Max results")
@add_auth_options
@handle_jira_error
def me(project, limit, org_url, email, api_key):
    """Show my open issues."""
    if not project:
        project = load_config().get("default_project")

    with make_client(org_url, email, api_key) as client:
        clauses = ["assignee = currentUser()", "statusCategory != Done"]
        if project:
            clauses.insert(0, f"project = {project}")
        jql = " AND ".join(clauses) + " ORDER BY updated DESC"
        result = client.search(
            jql,
            max_results=limit,
            fields=["summary", "status", "assignee", "priority", "issuetype"],
        )

    issues = result.get("issues", [])
    total = result.get("total", 0)
    title = f"My open issues — {len(issues)} of {total}"
    print_issue_table(issues, title=title)
