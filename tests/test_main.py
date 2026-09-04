import hashlib
import hmac
import json
import time
from unittest.mock import patch, MagicMock

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_app


@pytest.fixture
def app():
    with patch("app.main.SheetsClient"), \
         patch("app.main.SlackClient"), \
         patch("app.main.GeminiClient"):
        yield create_app()


@pytest.mark.asyncio
async def test_health(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_slack_url_verification(app):
    body = json.dumps({"type": "url_verification", "challenge": "test-challenge"})
    timestamp = str(int(time.time()))
    sig = _sign(body, timestamp)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/slack/events",
            content=body,
            headers={
                "X-Slack-Request-Timestamp": timestamp,
                "X-Slack-Signature": sig,
                "Content-Type": "application/json",
            },
        )
    assert response.status_code == 200
    assert response.json()["challenge"] == "test-challenge"


@pytest.mark.asyncio
async def test_slack_events_invalid_signature(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/slack/events",
            content=b'{"type":"event_callback"}',
            headers={
                "X-Slack-Request-Timestamp": str(int(time.time())),
                "X-Slack-Signature": "v0=invalid",
                "Content-Type": "application/json",
            },
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_digest_generate_requires_auth(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/digest/generate")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_digest_generate_with_auth(app):
    with patch("app.main.generate_digest"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/digest/generate",
                headers={"Authorization": "Bearer test-secret"},
            )
    assert response.status_code == 200


def _sign(body: str, timestamp: str) -> str:
    sig_basestring = f"v0:{timestamp}:{body}".encode()
    return "v0=" + hmac.new(
        b"test-signing-secret", sig_basestring, hashlib.sha256
    ).hexdigest()


@pytest.mark.asyncio
async def test_digest_job_survives_late_trigger():
    """A swapping 1GB host stalls the loop; a 1s misfire grace window silently
    drops the whole week's digest (this happened on 2026-08-21)."""
    with patch("app.main.SheetsClient"), \
         patch("app.main.SlackClient"), \
         patch("app.main.GeminiClient"), \
         patch("app.main.AsyncIOScheduler") as mock_sched_cls:
        mock_scheduler = MagicMock()
        mock_sched_cls.return_value = mock_scheduler

        app = create_app()
        async with app.router.lifespan_context(app):
            pass

    _, kwargs = mock_scheduler.add_job.call_args
    assert kwargs.get("misfire_grace_time", 1) >= 600, (
        "add_job must widen misfire_grace_time; APScheduler defaults to 1 second "
        "and silently skips the job if the event loop stalls past it"
    )
    assert kwargs.get("coalesce") is True
