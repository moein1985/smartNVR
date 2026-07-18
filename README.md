# SmartNVR — Frigate Intelligence Platform

AI-powered surveillance analytics platform built on top of Frigate NVR.

## Architecture

Clean Architecture (Python backend) + Next.js web panel.

```
YOLO/
├── frigate-intelligence/     # Python backend (FastAPI + CLI + Bots)
├── frigate-web-panel/        # Next.js web UI (TypeScript + Tailwind)
├── Phase1-7 Roadmaps         # Detailed implementation roadmaps
└── Architecture_Proposal.md  # Full architecture document
```

## Phases

| Phase | Name | Status |
|-------|------|--------|
| 1 | CLI Text-to-SQL Agent | ✅ Complete |
| 2 | REST API (FastAPI) | ✅ Complete |
| 3 | Messaging Bots (Telegram + Bale) | ✅ Complete |
| 4 | Flutter Client | Planned |
| 5 | POS Integration & Analytics | ✅ Complete |
| 6 | Server Deployment (Docker) | ✅ Complete |
| 7 | Web UI (Next.js) | In Progress |

## Tech Stack

**Backend:** Python 3.12, FastAPI, Avalai LLM (OpenAI-compatible), SQLite, Docker  
**Frontend:** Next.js 15, TypeScript, TailwindCSS, React Query, openapi-fetch  
**Deployment:** Docker on Ubuntu (192.168.85.202:8088)

## Quick Start

```bash
# Backend
cd frigate-intelligence
uv sync
cp .env.example .env  # Fill in API keys
uv run frigate-ai serve --host 0.0.0.0 --port 8000

# Frontend
cd frigate-web-panel
npm install
npm run generate-api  # Generate types from backend OpenAPI spec
npm run dev
```
