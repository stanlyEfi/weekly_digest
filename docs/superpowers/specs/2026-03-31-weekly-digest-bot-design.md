# Weekly Digest Bot — Design Spec

## Overview

Standalone Python service replacing an n8n workflow. Collects weekly insights from colleagues via Slack, stores them in Google Sheets, and generates a structured digest every Friday at 18:00 using Gemini API.

**Host:** DigitalOcean droplet `209.38.97.244`, domain `copilot4.run`, nginx + SSL.

## Architecture

Single FastAPI process on the droplet behind nginx reverse proxy.

**Endpoints:**
- `POST /slack/events` — Slack Events API handler
- `POST /digest/generate` — manual digest trigger (protected with a shared secret via `Authorization` header)
- `GET /health` — health check

**Scheduled task:** APScheduler — Friday 18:00, triggers digest generation.

**External services:**
- Slack API (Events API inbound + Web API for reactions, user info, posting)
- Google Sheets API (read/write insights)
- Gemini API (digest summary generation)

**Configuration** via `.env`:
- `SLACK_BOT_TOKEN` — Slack bot OAuth token
- `SLACK_SIGNING_SECRET` — for verifying Slack request signatures
- `GOOGLE_SHEETS_CREDENTIALS_FILE` — path to service account JSON
- `SPREADSHEET_ID` — Google Sheets document ID (`1xRhhDxFughUBHxEO98aktxgtUX5yeOK76Yz8rIQBOe4`)
- `GEMINI_API_KEY` — Gemini API key
- `DIGEST_CHANNEL_ID` — Slack channel for posting digest (`C044KE0U4QG`)
- `INSIGHT_CHANNEL_ID` — Slack channel where insights are collected
- `DIGEST_CRON_DAY` — day of week (default: `fri`)
- `DIGEST_CRON_HOUR` — hour (default: `18`)
- `DIGEST_CRON_MINUTE` — minute (default: `0`)
- `ADMIN_SECRET` — shared secret for protecting manual endpoints (`/digest/generate`)

## Workflow 1: Collecting Insights

**Trigger:** Slack sends POST to `/slack/events` when a message is posted.

**Flow:**

1. Verify Slack request signature (`X-Slack-Signature` header)
2. Handle Slack URL verification challenge (initial setup handshake)
3. Respond 200 immediately (Slack requires response within 3 seconds)
4. Process message asynchronously via FastAPI background task:
   a. **Filter out:**
      - Empty messages
      - Bot messages (check `is_bot` via Slack `users.info`)
      - Messages from the digest channel (prevent self-recording)
   b. **Enrich** — call Slack `users.info` to get `real_name` and `title`
   c. **Save to Google Sheets** (Messages sheet): `user_id`, `username`, `role`, `text`, `timestamp`, `ts`, `channel`, `week_number`
   d. **React** with :+1: emoji on the original message

**Error handling:**
- `users.info` fails: save with `user_id` as username, empty role
- Google Sheets fails: log error, do not add reaction (so user knows it wasn't saved)

## Workflow 2: Digest Generation

**Triggers:**
- APScheduler cron: Friday 18:00
- Manual: `POST /digest/generate`

**Flow:**

1. Read all rows from Google Sheets (Messages sheet)
2. Filter: only entries with `timestamp` within last 7 days
3. If no insights found: post "На этой неделе инсайтов не было. Не забывайте делиться обновлениями!" to digest channel, stop
4. Aggregate:
   - Build insights list: `[index]. [username/role] text`
   - Compute stats: per-user message count and percentage
5. Call Gemini API:
   - System prompt: "Ты — ассистент продуктовой команды. Твоя задача — создавать структурированные еженедельные дайджесты на основе инсайтов от разных людей и команд. Новости можно разделять по командам, либо компоновать по смыслу. Важно: формат ответа без приветствий, сразу дайджест. Форматирование должно быть адаптировано для Slack, не md."
   - User prompt: insights list + "Создай структурированный дайджест."
6. Format final message: Gemini summary + stats block + sign-off
7. Post to digest channel via Slack API
8. Optionally mark processed rows in Sheets

**Error handling:**
- Gemini API fails: log error, post raw insights list without summary as fallback
- Google Sheets fails: log error, do not post anything

## User Resolution

Users are resolved from Slack API in real time (`users.info`). No hardcoded mapping. The `real_name` and `title` fields from Slack profile are used.

## Project Structure

```
weekly_digest/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, lifespan, scheduler setup
│   ├── config.py            # Settings from .env (pydantic-settings)
│   ├── slack_handler.py     # Slack event processing logic
│   ├── digest_generator.py  # Digest generation logic
│   ├── sheets_client.py     # Google Sheets read/write operations
│   ├── slack_client.py      # Slack API wrapper (users.info, reactions, posting)
│   └── gemini_client.py     # Gemini API wrapper
├── .env.example
├── requirements.txt
└── Dockerfile
```

## Deployment

- Docker container on the DO droplet
- Nginx reverse proxy: `copilot4.run` -> `localhost:8000`
- Run with `docker compose up -d`
- Uvicorn as ASGI server inside the container

## Dependencies

- `fastapi`, `uvicorn`
- `apscheduler`
- `google-api-python-client`, `google-auth`
- `google-generativeai`
- `slack-sdk`
- `pydantic-settings`
