# Weekly Digest — Claude Instructions

## Project
- Domain: gulevichdev.com
- Server: 209.38.97.244 (DO Amsterdam, Ubuntu 22.04, 1vCPU/1GB RAM + 2GB swap)
- **Repo on server is at `/app/weekly_digest`**
- GitHub repo: stanlyEfi/weekly_digest

## Shared Infrastructure — CRITICAL

This project shares a server with other projects (running_copilot, etc.).
A shared nginx-proxy container handles ports 80/443 for ALL domains.

**NEVER:**
- Add an nginx service to this docker-compose
- Bind ports 80 or 443 from any service
- Run `docker compose` from `/app/nginx-proxy/` unless explicitly asked
- Run `docker compose down` without specifying this project's directory

**Network:** This project joins external `proxy-net` network.
Web service is accessible as `digest-web:8000` on the shared network.

## Deploy
- Manual: `ssh root@209.38.97.244 "cd /app/weekly_digest && git pull origin main && docker compose up --build -d"`
- **Deploy only restarts THIS project's containers, not nginx or other projects**

## Stack
- Backend: FastAPI + Python 3.12
- AI: Google Generative AI (Gemini)
- Integrations: Slack SDK, Google Sheets API
- Scheduler: APScheduler (Friday 18:00)
- Infra: Docker + Cloudflare (Full strict)
