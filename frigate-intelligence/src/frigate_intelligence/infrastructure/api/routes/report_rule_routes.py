import logging

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel

from frigate_intelligence.domain.models.report_rule import ReportRule
from frigate_intelligence.domain.models.user_model import UserModel
from frigate_intelligence.infrastructure.api.routes.auth_routes import (
    require_admin_dependency,
)
from frigate_intelligence.infrastructure.config.report_rule_manager import (
    ReportRuleManager,
)
from frigate_intelligence.infrastructure.config.report_history_manager import (
    ReportHistoryManager,
)
from frigate_intelligence.infrastructure.scheduler.report_scheduler import (
    ReportScheduler,
)

logger = logging.getLogger(__name__)


class ReportRuleResponse(BaseModel):
    id: str
    name: str
    enabled: bool
    zones: list[str]
    cameras: list[str]
    labels: list[str]
    interval_hours: int
    timezone: str
    destination: str
    chat_id: str
    prompt_template: str
    include_summary: bool
    include_raw_data: bool
    created_at: str
    last_run: str
    last_status: str


class CreateReportRuleRequest(BaseModel):
    name: str
    enabled: bool = True
    zones: list[str] = []
    cameras: list[str] = []
    labels: list[str] = []
    interval_hours: int = 24
    timezone: str = "Asia/Tehran"
    destination: str = "telegram"
    chat_id: str = ""
    prompt_template: str = ""
    include_summary: bool = True
    include_raw_data: bool = False


class UpdateReportRuleRequest(BaseModel):
    name: str | None = None
    enabled: bool | None = None
    zones: list[str] | None = None
    cameras: list[str] | None = None
    labels: list[str] | None = None
    interval_hours: int | None = None
    timezone: str | None = None
    destination: str | None = None
    chat_id: str | None = None
    prompt_template: str | None = None
    include_summary: bool | None = None
    include_raw_data: bool | None = None


class HistoryEntryResponse(BaseModel):
    id: str
    rule_id: str
    rule_name: str
    executed_at: str
    status: str
    message_preview: str
    destination: str


def _rule_to_response(rule: ReportRule) -> ReportRuleResponse:
    return ReportRuleResponse(
        id=rule.id,
        name=rule.name,
        enabled=rule.enabled,
        zones=rule.zones,
        cameras=rule.cameras,
        labels=rule.labels,
        interval_hours=rule.interval_hours,
        timezone=rule.timezone,
        destination=rule.destination,
        chat_id=rule.chat_id,
        prompt_template=rule.prompt_template,
        include_summary=rule.include_summary,
        include_raw_data=rule.include_raw_data,
        created_at=rule.created_at,
        last_run=rule.last_run,
        last_status=rule.last_status,
    )


def _get_rule_manager(request: Request) -> ReportRuleManager:
    return request.app.state.rule_manager


def _get_history_manager(request: Request) -> ReportHistoryManager:
    return request.app.state.history_manager


def _get_scheduler(request: Request) -> ReportScheduler:
    return request.app.state.report_scheduler


def create_report_rule_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1/report-rules", tags=["report-rules"])

    @router.get("", response_model=list[ReportRuleResponse])
    async def list_rules(
        admin: UserModel = Depends(require_admin_dependency),
        rule_manager: ReportRuleManager = Depends(_get_rule_manager),
    ):
        rules = rule_manager.list_rules()
        return [_rule_to_response(r) for r in rules]

    @router.post("", response_model=ReportRuleResponse)
    async def create_rule(
        body: CreateReportRuleRequest = Body(...),
        admin: UserModel = Depends(require_admin_dependency),
        rule_manager: ReportRuleManager = Depends(_get_rule_manager),
        scheduler: ReportScheduler = Depends(_get_scheduler),
    ):
        rule = ReportRule(
            id="",
            name=body.name,
            enabled=body.enabled,
            zones=body.zones,
            cameras=body.cameras,
            labels=body.labels,
            interval_hours=body.interval_hours,
            timezone=body.timezone,
            destination=body.destination,
            chat_id=body.chat_id,
            prompt_template=body.prompt_template,
            include_summary=body.include_summary,
            include_raw_data=body.include_raw_data,
        )
        created = rule_manager.create_rule(rule)
        if created.enabled:
            scheduler.refresh_rule(created.id)
        return _rule_to_response(created)

    @router.get("/{rule_id}", response_model=ReportRuleResponse)
    async def get_rule(
        rule_id: str,
        admin: UserModel = Depends(require_admin_dependency),
        rule_manager: ReportRuleManager = Depends(_get_rule_manager),
    ):
        rule = rule_manager.get_by_id(rule_id)
        if not rule:
            raise HTTPException(status_code=404, detail="Rule not found")
        return _rule_to_response(rule)

    @router.put("/{rule_id}", response_model=ReportRuleResponse)
    async def update_rule(
        rule_id: str,
        body: UpdateReportRuleRequest = Body(...),
        admin: UserModel = Depends(require_admin_dependency),
        rule_manager: ReportRuleManager = Depends(_get_rule_manager),
        scheduler: ReportScheduler = Depends(_get_scheduler),
    ):
        updates = {k: v for k, v in body.model_dump().items() if v is not None}
        try:
            updated = rule_manager.update_rule(rule_id, updates)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        scheduler.refresh_rule(rule_id)
        return _rule_to_response(updated)

    @router.delete("/{rule_id}")
    async def delete_rule(
        rule_id: str,
        admin: UserModel = Depends(require_admin_dependency),
        rule_manager: ReportRuleManager = Depends(_get_rule_manager),
        scheduler: ReportScheduler = Depends(_get_scheduler),
    ):
        try:
            rule_manager.delete_rule(rule_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        scheduler.remove_rule(rule_id)
        return {"status": "ok", "message": "Rule deleted"}

    @router.post("/{rule_id}/test")
    async def test_rule(
        rule_id: str,
        admin: UserModel = Depends(require_admin_dependency),
        scheduler: ReportScheduler = Depends(_get_scheduler),
    ):
        try:
            result = await scheduler.execute_rule_now(rule_id)
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return result

    @router.get("/{rule_id}/history", response_model=list[HistoryEntryResponse])
    async def get_rule_history(
        rule_id: str,
        admin: UserModel = Depends(require_admin_dependency),
        history_manager: ReportHistoryManager = Depends(_get_history_manager),
    ):
        entries = history_manager.list_by_rule(rule_id)
        return [
            HistoryEntryResponse(
                id=e.id,
                rule_id=e.rule_id,
                rule_name=e.rule_name,
                executed_at=e.executed_at,
                status=e.status,
                message_preview=e.message_preview,
                destination=e.destination,
            )
            for e in entries
        ]

    @router.get("/history/all", response_model=list[HistoryEntryResponse])
    async def get_all_history(
        admin: UserModel = Depends(require_admin_dependency),
        history_manager: ReportHistoryManager = Depends(_get_history_manager),
    ):
        entries = history_manager.list_entries()
        return [
            HistoryEntryResponse(
                id=e.id,
                rule_id=e.rule_id,
                rule_name=e.rule_name,
                executed_at=e.executed_at,
                status=e.status,
                message_preview=e.message_preview,
                destination=e.destination,
            )
            for e in entries
        ]

    return router
