from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import requests


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ai_signal_routine.sources import SourceCollector


class GitHubSourceTests(unittest.TestCase):
    def test_rejected_token_retries_without_authorization(self) -> None:
        collector = SourceCollector()
        response = requests.Response()
        response.status_code = 401
        error = requests.HTTPError("401 Client Error", response=response)
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer rejected-token",
        }

        with patch.object(
            collector,
            "_request_json",
            side_effect=[error, {"items": []}],
        ) as request_json:
            payload = collector._request_github_json(
                "https://api.github.com/search/repositories", headers, "GitHub Radar"
            )

        self.assertEqual(payload, {"items": []})
        self.assertTrue(collector.github_auth_disabled)
        self.assertNotIn("Authorization", request_json.call_args_list[1].kwargs["headers"])
        self.assertIn("Falling back to unauthenticated", collector.errors[0])

    def test_rate_limit_detection_uses_github_headers(self) -> None:
        response = requests.Response()
        response.status_code = 403
        response.headers["X-RateLimit-Remaining"] = "0"
        error = requests.HTTPError("403 Client Error", response=response)

        self.assertTrue(SourceCollector._is_rate_limit_error(error))

    def test_github_headers_trim_wrapped_token(self) -> None:
        collector = SourceCollector()
        with patch.dict(os.environ, {"GITHUB_TOKEN": "  'token-value'  "}, clear=False):
            headers = collector._github_headers()

        self.assertEqual(headers["Authorization"], "Bearer token-value")


if __name__ == "__main__":
    unittest.main()
