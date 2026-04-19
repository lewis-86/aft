import json
import urllib.request
from urllib.error import URLError


class GitHubCommentPoster:
    def __init__(self, token: str, repo: str, api_url: str = "https://api.github.com"):
        self.token = token
        self.repo = repo
        self.api_url = api_url

    def post_comment(self, pr_number: int, body: str) -> bool:
        url = self._build_url(pr_number)
        headers = self._build_headers()
        data = json.dumps({"body": body}).encode("utf-8")

        try:
            request = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(request) as response:
                return response.status == 201
        except Exception:
            return False

    def _build_url(self, pr_number: int) -> str:
        return f"{self.api_url}/repos/{self.repo}/issues/{pr_number}/comments"

    def _build_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
