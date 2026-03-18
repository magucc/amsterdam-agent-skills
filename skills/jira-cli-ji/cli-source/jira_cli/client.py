import base64
from typing import Any, Optional

import httpx


class JiraError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(message)


class JiraClient:
    def __init__(self, org_url: str, email: str, api_key: str):
        self.base_url = org_url.rstrip("/") + "/rest/api/3"
        token = base64.b64encode(f"{email}:{api_key}".encode()).decode()
        self._client = httpx.Client(
            headers={
                "Authorization": f"Basic {token}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = f"{self.base_url}{path}"
        resp = self._client.request(method, url, **kwargs)
        self._raise_for_status(resp)
        if resp.status_code == 204 or not resp.content:
            return None
        return resp.json()

    def _raise_for_status(self, resp: httpx.Response) -> None:
        if resp.is_success:
            return
        if resp.status_code == 401:
            raise JiraError(401, "Unauthorized — check your email and API key.")
        if resp.status_code == 403:
            raise JiraError(403, "Forbidden — you don't have permission for this action.")
        if resp.status_code == 404:
            raise JiraError(404, "Not found — issue or resource does not exist.")
        if resp.status_code == 429:
            raise JiraError(429, "Rate limited — too many requests, try again shortly.")
        try:
            body = resp.json()
            messages = body.get("errorMessages", [])
            errors = body.get("errors", {})
            detail = "; ".join(messages) or "; ".join(f"{k}: {v}" for k, v in errors.items())
        except Exception:
            detail = resp.text[:200]
        raise JiraError(resp.status_code, detail or f"HTTP {resp.status_code}")

    # --- Projects ---

    def get_projects(self) -> list[dict]:
        return self._request("GET", "/project/search", params={"maxResults": 100}).get("values", [])

    # --- Issue ---

    def get_issue(self, issue_key: str) -> dict:
        return self._request("GET", f"/issue/{issue_key}")

    def update_issue(self, issue_key: str, fields: dict, update: dict | None = None) -> None:
        body: dict[str, Any] = {"fields": fields}
        if update:
            body["update"] = update
        self._request("PUT", f"/issue/{issue_key}", json=body)

    def create_issue(self, project_key: str, summary: str, issue_type: str = "Task",
                     description: str = "", labels: list[str] | None = None,
                     priority: str | None = None, assignee_id: str | None = None) -> dict:
        fields: dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
        if description:
            fields["description"] = {
                "type": "doc", "version": 1,
                "content": [{"type": "paragraph", "content": [{"type": "text", "text": description}]}],
            }
        if labels:
            fields["labels"] = labels
        if priority:
            fields["priority"] = {"name": priority}
        if assignee_id:
            fields["assignee"] = {"accountId": assignee_id}
        return self._request("POST", "/issue", json={"fields": fields})

    # --- Transitions ---

    def get_transitions(self, issue_key: str) -> list[dict]:
        data = self._request("GET", f"/issue/{issue_key}/transitions")
        return data.get("transitions", [])

    def transition_issue(self, issue_key: str, transition_id: str) -> None:
        self._request(
            "POST",
            f"/issue/{issue_key}/transitions",
            json={"transition": {"id": transition_id}},
        )

    # --- Comments ---

    def add_comment(self, issue_key: str, body_text: str) -> dict:
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": body_text}],
                    }
                ],
            }
        }
        return self._request("POST", f"/issue/{issue_key}/comment", json=payload)

    # --- Search ---

    def search(
        self,
        jql: str,
        max_results: int = 20,
        fields: Optional[list[str]] = None,
    ) -> dict:
        params: dict[str, Any] = {"jql": jql, "maxResults": max_results}
        if fields:
            params["fields"] = ",".join(fields)
        return self._request("GET", "/search/jql", params=params)

    # --- Assignee ---

    def find_user_by_email(self, email: str) -> Optional[dict]:
        data = self._request("GET", "/user/search", params={"query": email})
        if data:
            return data[0]
        return None

    def get_myself(self) -> dict:
        return self._request("GET", "/myself")

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
