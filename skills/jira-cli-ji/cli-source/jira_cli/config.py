import json
import os
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path.home() / ".jira-cli.json"


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f)
    return {}


def save_config(org_url: str, email: str, api_key: str, default_project: str = "") -> None:
    config = {
        "org_url": org_url.rstrip("/"),
        "email": email,
        "api_key": api_key,
        "default_project": default_project,
    }
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)
    os.chmod(CONFIG_PATH, 0o600)


def resolve_config(
    org_url: Optional[str],
    email: Optional[str],
    api_key: Optional[str],
) -> tuple[str, str, str]:
    """Merge CLI flags over config file. Raises if any value is missing."""
    file_cfg = load_config()

    resolved_url = org_url or file_cfg.get("org_url")
    resolved_email = email or file_cfg.get("email")
    resolved_key = api_key or file_cfg.get("api_key")

    missing = []
    if not resolved_url:
        missing.append("--org-url")
    if not resolved_email:
        missing.append("--email")
    if not resolved_key:
        missing.append("--api-key")

    if missing:
        raise ValueError(
            f"Missing required config: {', '.join(missing)}. "
            "Run `jira configure` or pass flags."
        )

    return resolved_url.rstrip("/"), resolved_email, resolved_key
