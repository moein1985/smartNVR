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


@dataclass
class TextToSQLResponse:
    question: str
    sql: str
    result: QueryResult
    explanation: str
    attempts: int


@dataclass
class TextToSQLStreamResult:
    question: str
    sql: str
    result: QueryResult
    attempts: int
    explanation_stream: Generator[str, None, None]


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
        system_prompt = self._prompt.as_system_prompt()
        attempts = 0
        last_error = ""
        question = self._enrich_question(request.question)
        logger.info(f"Query received: {request.question}")
        if question != request.question:
            logger.info(f"Question enriched: {question}")

        for attempt in range(1, request.max_retries + 1):
            attempts = attempt
            user_msg = (
                question
                if attempt == 1
                else f"{question}\n\nPrevious attempt failed: {last_error}\nPlease fix the SQL."
            )

            sql_raw = self._llm.generate_sql(user_msg, system_prompt)
            sql = self._extract_sql(sql_raw)
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
        )

    def execute_streaming(self, request: TextToSQLRequest) -> TextToSQLStreamResult:
        system_prompt = self._prompt.as_system_prompt()
        attempts = 0
        last_error = ""
        logger.info(f"Stream query received: {request.question}")

        for attempt in range(1, request.max_retries + 1):
            attempts = attempt
            user_msg = (
                request.question
                if attempt == 1
                else f"{request.question}\n\nPrevious attempt failed: {last_error}\nPlease fix the SQL."
            )

            sql_raw = self._llm.generate_sql(user_msg, system_prompt)
            sql = self._extract_sql(sql_raw)
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
        )

    def _extract_sql(self, raw: str) -> str:
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = [line for line in lines if not line.startswith("```")]
            return "\n".join(lines).strip()
        return raw

    def _enrich_question(self, question: str) -> str:
        """Inject sub_label hints when person names are detected in the question."""
        import re
        known_names = ["moein", "soleymani", "ahmad", "ali", "reza", "sara"]
        question_lower = question.lower()
        hints = []
        for name in known_names:
            if re.search(r'\b' + name + r'\b', question_lower):
                hints.append(
                    f"NOTE: '{name}' is a person name. Filter using sub_label LIKE '%{name}%' (NOT label='{name}'). "
                    f"The label column only contains object classes like 'person'."
                )
        if any(w in question_lower for w in ["who was seen", "who came", "who visited", "who appeared"]):
            hints.append("NOTE: To find recognized persons, query DISTINCT sub_label WHERE sub_label IS NOT NULL.")
        if any(w in question_lower for w in ["unknown face", "unknown person", "unrecognized", "unknown people"]):
            hints.append("NOTE: Unknown/unrecognized faces have sub_label='unknown'.")
        if hints:
            return f"{question}\n\n{' '.join(hints)}"
        return question

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
