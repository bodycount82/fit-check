"""Tests for youcam_client.py — mocked API interactions.

These tests verify the client's protocol logic (upload → submit → poll)
without hitting the real API. The real API is exercised when the demo runs live.
"""

from __future__ import annotations

import os
import tempfile
from typing import Any
from unittest.mock import MagicMock

import pytest

from youcam_client import YouCamClient, YouCamError


class FakeSession:
    """A requests.Session that returns endpoint-appropriate canned responses.

    The real API is three different endpoints, so a single canned reply cannot
    model it. This fake dispatches on the URL so the client's real protocol
    logic (upload → submit → poll) is what gets tested.

    Overrides are settable via `post_override`, `get_override`, `put_override`
    so a test can simulate a failure without monkeypatching bound methods
    (which do not have a settable `return_value`).
    """

    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict]] = []
        self.post_override: MagicMock | None = None
        self.get_override: MagicMock | None = None
        self.put_override: MagicMock | None = None

    @staticmethod
    def _resp(status: int, payload: dict | None = None, text: str = "") -> MagicMock:
        mock = MagicMock()
        mock.status_code = status
        mock.text = text
        if payload is not None:
            mock.json.return_value = payload
        return mock

    def post(self, url: str, **kwargs: Any) -> MagicMock:
        self.calls.append(("POST", url, kwargs))
        if self.post_override is not None:
            return self.post_override
        if url.endswith("/s2s/v2.0/file"):
            return self._resp(200, {
                "result": {
                    "files": [
                        {
                            "requests": {"url": "https://upload.test/img.jpg"},
                            "file_id": "f1",
                        }
                    ]
                }
            })
        # Task submission endpoint
        return self._resp(200, {"result": {"task_id": "t1"}})

    def put(self, url: str, **kwargs: Any) -> MagicMock:
        self.calls.append(("PUT", url, kwargs))
        if self.put_override is not None:
            return self.put_override
        return self._resp(200)

    def get(self, url: str, **kwargs: Any) -> MagicMock:
        self.calls.append(("GET", url, kwargs))
        if self.get_override is not None:
            return self.get_override
        return self._resp(200, {
            "result": {"task_status": "success", "url": "https://result.test/img.jpg"}
        })


@pytest.fixture
def image_file() -> str:
    """A real file on disk, because upload_file actually opens the path."""
    fd, path = tempfile.mkstemp(suffix=".jpg")
    with os.fdopen(fd, "wb") as fh:
        fh.write(b"\xff\xd8\xff\xe0fake-jpeg-bytes")
    yield path
    os.unlink(path)


class TestYouCamClientUpload:
    """The upload step: get presigned URL, PUT bytes."""

    def test_upload_returns_file_id(self, image_file: str):
        session = FakeSession()
        client = YouCamClient(api_key="test", session=session)
        file_id = client.upload_file(image_file)
        assert file_id == "f1"
        assert len(session.calls) == 2  # POST (file API) + PUT (bytes)

    def test_upload_uses_correct_endpoint(self, image_file: str):
        session = FakeSession()
        client = YouCamClient(api_key="test", session=session)
        client.upload_file(image_file)
        assert session.calls[0][0] == "POST"
        assert "/s2s/v2.0/file" in session.calls[0][1]
        assert session.calls[1][0] == "PUT"
        assert "upload.test" in session.calls[1][1]

    def test_upload_sends_bearer_auth(self, image_file: str):
        session = FakeSession()
        client = YouCamClient(api_key="secret-key", session=session)
        client.upload_file(image_file)
        headers = session.calls[0][2].get("headers", {})
        assert headers.get("Authorization") == "Bearer secret-key"

    def test_no_api_key_raises(self):
        with pytest.raises(YouCamError, match="No YouCam API key"):
            YouCamClient(api_key=None)

    def test_missing_file_raises(self):
        session = FakeSession()
        client = YouCamClient(api_key="test", session=session)
        with pytest.raises(FileNotFoundError):
            client.upload_file("/nonexistent/definitely-not-here.jpg")


class TestYouCamClientTask:
    """Submit → poll cycle."""

    def test_successful_task(self):
        session = FakeSession()
        client = YouCamClient(api_key="test", session=session)
        result = client.run_task("skin-analysis", {"src_file_id": "f1"})
        assert result.ok
        assert result.task_id == "t1"
        assert result.result_url == "https://result.test/img.jpg"

    def test_task_posts_to_feature_endpoint(self):
        session = FakeSession()
        client = YouCamClient(api_key="test", session=session)
        client.run_task("skin-analysis", {"src_file_id": "f1"})
        assert "/s2s/v2.0/task/skin-analysis" in session.calls[0][1]

    def test_error_task_returns_error_not_raise(self):
        """Failed tasks cost nothing — report, don't raise."""
        session = FakeSession()
        session.get_override = FakeSession._resp(
            200, {"result": {"task_status": "error", "error_message": "bad image"}}
        )
        client = YouCamClient(api_key="test", session=session)
        result = client.run_task("skin-analysis", {"src_file_id": "f1"})
        assert result.status == "error"
        assert not result.ok

    def test_timeout_raises(self):
        """If the task never finishes, raise after max_polls."""
        session = FakeSession()
        session.get_override = FakeSession._resp(
            200, {"result": {"task_status": "processing"}}
        )
        client = YouCamClient(api_key="test", session=session, sleep=lambda _x: None)
        with pytest.raises(YouCamError, match="did not finish"):
            client.run_task("skin-analysis", {"src_file_id": "f1"}, max_polls=3)

    def test_submit_error_raises(self):
        """If the submit itself fails, raise immediately."""
        session = FakeSession()
        session.post_override = FakeSession._resp(400, text="invalid payload")
        client = YouCamClient(api_key="test", session=session)
        with pytest.raises(YouCamError, match="submit"):
            client.run_task("skin-analysis", {"src_file_id": "f1"})


class TestYouCamClientHelpers:
    """Convenience wrappers: skin_analysis, clothes_vto, ring_vto."""

    def test_skin_analysis_wraps_run_task(self):
        session = FakeSession()
        client = YouCamClient(api_key="test", session=session)
        result = client.skin_analysis("f1", concerns=["redness", "pore"], hd=True)
        assert result.ok
        payload = session.calls[0][2].get("json", {})
        assert payload.get("src_file_id") == "f1"
        assert payload.get("miniserver_version") == "2.1"

    def test_skin_analysis_sd_uses_20(self):
        session = FakeSession()
        client = YouCamClient(api_key="test", session=session)
        client.skin_analysis("f1", hd=False)
        payload = session.calls[0][2].get("json", {})
        assert payload.get("miniserver_version") == "2.0"

    def test_clothes_vto_wraps_run_task(self):
        session = FakeSession()
        client = YouCamClient(api_key="test", session=session)
        client.clothes_vto("f1", "g1")
        payload = session.calls[0][2].get("json", {})
        assert payload.get("src_file_id") == "f1"
        assert payload.get("ref_file_id") == "g1"
        assert "/task/cloth" in session.calls[0][1]

    def test_ring_vto_wraps_run_task(self):
        session = FakeSession()
        client = YouCamClient(api_key="test", session=session)
        client.ring_vto("f1", "r1")
        payload = session.calls[0][2].get("json", {})
        assert payload.get("src_file_id") == "f1"
        assert payload.get("ref_file_id") == "r1"
        assert "/task/ring" in session.calls[0][1]


class TestClientFromEnv:
    """The factory function."""

    def test_raises_without_key(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("YOUCAM_API_KEY", raising=False)
        from youcam_client import client_from_env

        with pytest.raises(YouCamError, match="No YouCam API key"):
            client_from_env()

    def test_reads_key_from_env(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("YOUCAM_API_KEY", "from-env")
        from youcam_client import client_from_env

        client = client_from_env()
        assert client.api_key == "from-env"
