import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import BackgroundTasks, FastAPI, Request, Response

from app.config import Settings
from app.digest_generator import generate_digest
from app.gemini_client import GeminiClient
from app.sheets_client import SheetsClient
from app.slack_client import SlackClient
from app.slack_handler import process_message, verify_slack_signature

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    settings = Settings()

    slack_client = SlackClient(settings.slack_bot_token)
    sheets_client = SheetsClient(
        settings.google_sheets_credentials_file, settings.spreadsheet_id
    )
    gemini_client = GeminiClient(settings.gemini_api_key)

    scheduler = AsyncIOScheduler()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        scheduler.add_job(
            _run_digest,
            "cron",
            day_of_week=settings.digest_cron_day,
            hour=settings.digest_cron_hour,
            minute=settings.digest_cron_minute,
        )
        scheduler.start()
        logger.info(
            "Scheduler started: digest at %s %02d:%02d",
            settings.digest_cron_day,
            settings.digest_cron_hour,
            settings.digest_cron_minute,
        )
        yield
        scheduler.shutdown()

    app = FastAPI(lifespan=lifespan)

    def _run_digest():
        generate_digest(sheets_client, gemini_client, slack_client, settings.digest_channel_id)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/slack/events")
    async def slack_events(request: Request, background_tasks: BackgroundTasks):
        body = await request.body()
        timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
        signature = request.headers.get("X-Slack-Signature", "")

        if not verify_slack_signature(settings.slack_signing_secret, body, timestamp, signature):
            return Response(status_code=403)

        payload = await request.json()

        if payload.get("type") == "url_verification":
            return {"challenge": payload["challenge"]}

        event = payload.get("event", {})
        if event.get("type") == "message" and "subtype" not in event:
            background_tasks.add_task(
                process_message, event, slack_client, sheets_client, settings.digest_channel_id
            )

        return Response(status_code=200)

    @app.post("/digest/generate")
    async def manual_digest(request: Request, background_tasks: BackgroundTasks):
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {settings.admin_secret}":
            return Response(status_code=401)

        background_tasks.add_task(_run_digest)
        return {"status": "digest generation started"}

    return app
