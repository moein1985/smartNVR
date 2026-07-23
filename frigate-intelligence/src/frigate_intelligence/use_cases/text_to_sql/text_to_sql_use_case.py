import logging
from dataclasses import dataclass
from typing import Generator

from frigate_intelligence.domain.repositories.frigate_repository import FrigateRepository
from frigate_intelligence.domain.services.llm_service import LLMService
from frigate_intelligence.domain.entities.query_result import QueryResult
from frigate_intelligence.use_cases.text_to_sql.sql_validator import SQLValidator
from frigate_intelligence.use_cases.text_to_sql.prompt_builder import PromptBuilder

logger = logging.getLogger(__name__)


@dataclass
class TextToSQLRequest:
    question: str
    max_retries: int = 3
    client_tz_info: dict | None = None
    work_hours_start: str | None = None
    work_hours_end: str | None = None


@dataclass
class TextToSQLResponse:
    question: str
    sql: str
    result: QueryResult
    explanation: str
    attempts: int
    intent: str = "event_query"
    playback_intent: dict | None = None


@dataclass
class TextToSQLStreamResult:
    question: str
    sql: str
    result: QueryResult
    attempts: int
    explanation_stream: Generator[str, None, None]
    intent: str = "event_query"
    playback_intent: dict | None = None


class TextToSQLUseCase:
    def __init__(
        self,
        frigate_repo: FrigateRepository,
        llm_service: LLMService,
    ):
        self._repo = frigate_repo
        self._llm = llm_service
        self._prompt = PromptBuilder.build()

    def execute(self, request: TextToSQLRequest) -> TextToSQLResponse:
        if request.client_tz_info or request.work_hours_start:
            prompt = PromptBuilder.build(
                request.client_tz_info,
                work_hours_start=request.work_hours_start,
                work_hours_end=request.work_hours_end,
            )
            system_prompt = prompt.as_system_prompt()
            logger.info("[TimeSync] Prompt rebuilt with client timezone and/or working hours context")
        else:
            system_prompt = self._prompt.as_system_prompt()
        logger.info(f"Query received: {request.question}")

        smart = self._llm.smart_query(request.question, system_prompt)
        intent = smart.get("intent", "event_query")
        logger.info(f"Smart query intent: {intent}")

        if intent == "playback_query":
            playback = self._build_playback_intent(smart)
            explanation = smart.get("explanation", "Playback requested.")
            logger.info(f"Playback intent: {playback}")
            return TextToSQLResponse(
                question=request.question,
                sql="",
                result=QueryResult(
                    sql="",
                    columns=[],
                    rows=[],
                    row_count=0,
                ),
                explanation=explanation,
                attempts=1,
                intent="playback_query",
                playback_intent=playback,
            )

        sql = self._extract_sql(smart.get("sql", ""))
        attempts = 0
        last_error = ""

        for attempt in range(1, request.max_retries + 1):
            attempts = attempt
            user_msg = (
                request.question
                if attempt == 1
                else f"{request.question}\n\nPrevious attempt failed: {last_error}\nPlease fix the SQL."
            )

            if attempt == 1:
                sql_raw = sql
            else:
                sql_raw = self._llm.generate_sql(user_msg, system_prompt)
                sql_raw = self._extract_sql(sql_raw)
            sql = sql_raw
            logger.info(f"Attempt {attempts} - Generated SQL: {sql}")

            is_valid, error = SQLValidator.validate(sql)
            if not is_valid:
                last_error = f"Validation: {error}"
                logger.warning(f"Attempt {attempts} - Validation error: {error}")
                continue

            result = self._repo.execute_sql(sql)
            if not result.is_success:
                last_error = f"Execution: {result.error}"
                logger.warning(f"Attempt {attempts} - SQL execution error: {result.error}")
                continue

            result_text = self._format_result(result)
            explanation = self._llm.explain_result(request.question, sql, result_text)
            logger.info(f"Query succeeded: {result.row_count} rows, attempts={attempts}")
            return TextToSQLResponse(
                question=request.question,
                sql=sql,
                result=result,
                explanation=explanation,
                attempts=attempts,
                intent="event_query",
            )

        logger.error(f"Query failed after {attempts} attempts. Last error: {last_error}")
        return TextToSQLResponse(
            question=request.question,
            sql="",
            result=QueryResult(
                sql="",
                columns=[],
                rows=[],
                row_count=0,
                error=last_error,
            ),
            explanation=f"Failed after {attempts} attempts. Last error: {last_error}",
            attempts=attempts,
            intent="event_query",
        )

    def execute_streaming(self, request: TextToSQLRequest) -> TextToSQLStreamResult:
        if request.client_tz_info or request.work_hours_start:
            prompt = PromptBuilder.build(
                request.client_tz_info,
                work_hours_start=request.work_hours_start,
                work_hours_end=request.work_hours_end,
            )
            system_prompt = prompt.as_system_prompt()
            logger.info("[TimeSync] Stream prompt rebuilt with client timezone and/or working hours context")
        else:
            system_prompt = self._prompt.as_system_prompt()
        logger.info(f"Stream query received: {request.question}")

        smart = self._llm.smart_query(request.question, system_prompt)
        intent = smart.get("intent", "event_query")
        logger.info(f"Stream smart query intent: {intent}")

        if intent == "playback_query":
            playback = self._build_playback_intent(smart)
            explanation = smart.get("explanation", "Playback requested.")
            logger.info(f"Stream playback intent: {playback}")
            return TextToSQLStreamResult(
                question=request.question,
                sql="",
                result=QueryResult(
                    sql="",
                    columns=[],
                    rows=[],
                    row_count=0,
                ),
                attempts=1,
                explanation_stream=iter([explanation]),
                intent="playback_query",
                playback_intent=playback,
            )

        sql = self._extract_sql(smart.get("sql", ""))
        attempts = 0
        last_error = ""

        for attempt in range(1, request.max_retries + 1):
            attempts = attempt
            user_msg = (
                request.question
                if attempt == 1
                else f"{request.question}\n\nPrevious attempt failed: {last_error}\nPlease fix the SQL."
            )

            if attempt == 1:
                sql_raw = sql
            else:
                sql_raw = self._llm.generate_sql(user_msg, system_prompt)
                sql_raw = self._extract_sql(sql_raw)
            sql = sql_raw
            logger.info(f"Attempt {attempts} - Generated SQL: {sql}")

            is_valid, error = SQLValidator.validate(sql)
            if not is_valid:
                last_error = f"Validation: {error}"
                logger.warning(f"Attempt {attempts} - Validation error: {error}")
                continue

            result = self._repo.execute_sql(sql)
            if not result.is_success:
                last_error = f"Execution: {result.error}"
                logger.warning(f"Attempt {attempts} - SQL execution error: {result.error}")
                continue

            result_text = self._format_result(result)
            stream = self._llm.explain_result_stream(request.question, sql, result_text)
            logger.info(f"Stream query succeeded: {result.row_count} rows, attempts={attempts}")
            return TextToSQLStreamResult(
                question=request.question,
                sql=sql,
                result=result,
                attempts=attempts,
                explanation_stream=stream,
                intent="event_query",
            )

        logger.error(f"Stream query failed after {attempts} attempts. Last error: {last_error}")
        return TextToSQLStreamResult(
            question=request.question,
            sql="",
            result=QueryResult(
                sql="",
                columns=[],
                rows=[],
                row_count=0,
                error=last_error,
            ),
            attempts=attempts,
            explanation_stream=iter([f"Failed after {attempts} attempts. Last error: {last_error}"]),
            intent="event_query",
        )

    def _extract_sql(self, raw: str) -> str:
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = [line for line in lines if not line.startswith("```")]
            return "\n".join(lines).strip()
        return raw

    def _build_playback_intent(self, smart: dict) -> dict:
        """Extract playback intent fields from smart_query JSON response."""
        import datetime as dt

        camera = smart.get("camera") or "cam1"
        start_str = smart.get("start_time")
        end_str = smart.get("end_time")

        start_time = 0.0
        end_time = 0.0
        date_str = ""

        if start_str:
            try:
                start_time = dt.datetime.fromisoformat(start_str).timestamp()
                date_str = dt.datetime.fromisoformat(start_str).strftime("%Y-%m-%d")
            except (ValueError, TypeError):
                pass
        if end_str:
            try:
                end_time = dt.datetime.fromisoformat(end_str).timestamp()
            except (ValueError, TypeError):
                pass

        if not date_str:
            date_str = dt.date.today().isoformat()

        return {
            "camera": camera,
            "start_time": start_time,
            "end_time": end_time,
            "date": date_str,
        }

    def _format_result(self, result: QueryResult) -> str:
        if not result.columns:
            return f"({result.row_count} rows)"
        header = " | ".join(result.columns)
        separator = "-" * len(header)
        data_lines = []
        for row in result.rows[:20]:
            data_lines.append(" | ".join(str(v) for v in row))
        return (
            f"{header}\n{separator}\n"
            + "\n".join(data_lines)
            + f"\n({result.row_count} rows total)"
        )
