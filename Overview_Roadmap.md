# Frigate Intelligence Platform — Master Roadmap

## Project Overview

**Frigate Intelligence Platform** is an AI-powered surveillance analytics system that sits on top of Frigate NVR. It enables natural language querying of camera events, automated notifications, POS transaction correlation, and cross-platform client access.

---

## Architecture Summary

**Pattern**: Clean Architecture (Dependency Rule: inward only)

```
Frameworks & Drivers (FastAPI, CLI, Telegram, Bale, Avalai, SQLite, POS)
        ↓
Interface Adapters (Controllers, Presenters, Schemas)
        ↓
Use Cases (Text-to-SQL, Event Query, POS Correlation, Notifications)
        ↓
Domain (Entities, Repository Interfaces, Service Interfaces)
```

**Key Principle**: Domain layer has ZERO external dependencies. All infrastructure (DB, LLM, bots) implements interfaces defined in Domain.

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend Language | Python 3.12+ |
| Package Manager | uv |
| CLI Framework | Typer + Rich |
| Web Framework | FastAPI |
| LLM Orchestration | LangChain (ReAct Agent) |
| LLM API | Avalai.ir (OpenAI-compatible, Gemini 3.1 Flash Lite) |
| Database | SQLite (Frigate DB) |
| Bot Framework | python-telegram-bot, Bale API |
| Mobile/Desktop | Flutter |
| Testing | pytest, pytest-asyncio |

---

## Phase Summary

| Phase | Name | Status | Roadmap File |
|-------|------|--------|-------------|
| 1 | CLI Text-to-SQL Agent | ✅ Complete | [Phase1_CLI_Agent_Roadmap.md](Phase1_CLI_Agent_Roadmap.md) |
| 2 | REST API (FastAPI) | ✅ Complete | [Phase2_REST_API_Roadmap.md](Phase2_REST_API_Roadmap.md) |
| 3 | Messaging Bots (Telegram + Bale) | ✅ Complete | [Phase3_Bots_Roadmap.md](Phase3_Bots_Roadmap.md) |
| 4 | Flutter Client (Mobile + Desktop) | Planned | [Phase4_Flutter_Roadmap.md](Phase4_Flutter_Roadmap.md) |
| 5 | POS Integration & Analytics | ✅ Complete | [Phase5_POS_Integration_Roadmap.md](Phase5_POS_Integration_Roadmap.md) |
| 6 | Server Deployment (Docker) | ✅ Complete | [Phase6_Server_Deployment_Roadmap.md](Phase6_Server_Deployment_Roadmap.md) |

---

## Infrastructure Status (Pre-existing)

| Component | Status | Details |
|-----------|--------|---------|
| Frigate NVR | ✅ Deployed | v0.18.0-beta1-tensorrt on Proxmox (192.168.85.203) |
| GPU | ✅ Active | RTX 5050 (Blackwell), ONNX detector |
| Model | ✅ Loaded | YOLOv9-t-320 (yolo-generic, ONNX) |
| Camera | ✅ Streaming | cam1 (RTSP 192.168.85.112:554) |
| Detection | ✅ Verified | 83+ person events recorded |
| Database | ✅ Accessible | SQLite at `/opt/frigate/config/frigate.db` |
| Schema | ✅ Extracted | See [Frigate_Database_Schema_Report.md](Frigate_Database_Schema_Report.md) |

---

## Project Directory Structure (Post-Cleanup)

```
C:\Users\Moein\Documents\Codes\YOLO\
├── Architecture_Proposal.md              # Full architecture document
├── Frigate_Database_Schema_Report.md     # DB schema for LLM context
├── Overview_Roadmap.md                   # This file
├── Phase1_CLI_Agent_Roadmap.md           # Phase 1 detailed roadmap
├── Phase2_REST_API_Roadmap.md            # Phase 2 detailed roadmap
├── Phase3_Bots_Roadmap.md                # Phase 3 detailed roadmap
├── Phase4_Flutter_Roadmap.md             # Phase 4 detailed roadmap
├── Phase5_POS_Integration_Roadmap.md     # Phase 5 detailed roadmap
├── Phase6_Server_Deployment_Roadmap.md   # Phase 6 detailed roadmap
├── frigate-config.yml                    # Frigate configuration (reference)
├── frigate-docker-compose.yml            # Docker compose (reference)
├── yolov9-t-320.onnx                     # ONNX model (reference)
├── yolov9t.pt                            # PyTorch model (reference)
├── Archive_Pre_Deployment/               # Old scripts (archived)
└── frigate-intelligence/                 # Backend project (Phases 1-3, 5 implemented)
```

---

## Development Workflow

1. **Each phase** has a dedicated roadmap file with step-by-step tasks, file paths, function signatures, and acceptance criteria.
2. **Implementation order**: Always follow the roadmap steps in sequence. Do not skip steps.
3. **Testing**: Every step has acceptance criteria that must be verified before proceeding.
4. **No hallucination**: Roadmap files contain exact file paths, function signatures, and expected behavior. Follow them precisely.
5. **Dependencies**: Each phase builds on the previous one. Phase 1 (Domain + Use Cases) is the foundation.

---

## Environment Variables (Required)

```env
# .env file (to be created in frigate-intelligence/)
FRIGATE_DB_PATH=/opt/frigate/config/frigate.db
AVALAI_API_KEY=<your-api-key>
AVALAI_BASE_URL=https://api.avalai.ir/v1
LLM_MODEL=gemini-3.1-flash-lite
TELEGRAM_BOT_TOKEN=<token>
BALE_BOT_TOKEN=<token>
POS_API_URL=<url>
POS_API_KEY=<key>
```
