from unittest.mock import patch

import pytest
from urllib.error import URLError

from aft.cli.github import GitHubCommentPoster


class TestGitHubCommentPoster:
    def test_post_comment_success(self):
        poster = GitHubCommentPoster(token="test-token", repo="owner/repo")
        with patch("aft.cli.github.urllib.request.urlopen") as mock_urlopen:
            mock_response = mock_urlopen.return_value.__enter__.return_value
            mock_response.status = 201
            mock_response.read.return_value = b'{"id": 1}'

            result = poster.post_comment(pr_number=123, body="Test comment")

            assert result is True
            mock_urlopen.assert_called_once()
            call_args = mock_urlopen.call_args
            assert call_args[0][0].full_url == "https://api.github.com/repos/owner/repo/issues/123/comments"

    def test_post_comment_failure(self):
        poster = GitHubCommentPoster(token="test-token", repo="owner/repo")
        with patch("aft.cli.github.urllib.request.urlopen") as mock_urlopen:
            mock_response = mock_urlopen.return_value.__enter__.return_value
            mock_response.status = 404

            result = poster.post_comment(pr_number=123, body="Test comment")

            assert result is False

    def test_post_comment_exception(self):
        poster = GitHubCommentPoster(token="test-token", repo="owner/repo")
        with patch("aft.cli.github.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = URLError("Network error")

            result = poster.post_comment(pr_number=123, body="Test comment")

            assert result is False

    def test_build_url(self):
        poster = GitHubCommentPoster(token="test-token", repo="owner/repo")
        url = poster._build_url(pr_number=456)
        assert url == "https://api.github.com/repos/owner/repo/issues/456/comments"

    def test_build_headers(self):
        poster = GitHubCommentPoster(token="test-token", repo="owner/repo")
        headers = poster._build_headers()
        assert headers["Authorization"] == "Bearer test-token"
        assert headers["Accept"] == "application/vnd.github+json"
        assert headers["X-GitHub-Api-Version"] == "2022-11-28"
