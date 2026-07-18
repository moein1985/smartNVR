from dataclasses import dataclass

from frigate_intelligence.domain.repositories.frigate_repository import FrigateRepository
from frigate_intelligence.domain.services.llm_service import LLMService
from frigate_intelligence.domain.entities.query_result import QueryResult
from frigate_intelligence.use_cases.text_to_sql.sql_validator import SQLValidator
from frigate_intelligence.use_cases.text_to_sql.prompt_builder import PromptBuilder


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

        for attempt in range(1, request.max_retries + 1):
            attempts = attempt
            user_msg = (
                request.question
                if attempt == 1
                else f"{request.question}\n\nPrevious attempt failed: {last_error}\nPlease fix the SQL."
            )

            sql_raw = self._llm.generate_sql(user_msg, system_prompt)
            sql = self._extract_sql(sql_raw)

            is_valid, error = SQLValidator.validate(sql)
            if not is_valid:
                last_error = f"Validation: {error}"
                continue

            result = self._repo.execute_sql(sql)
            if not result.is_success:
                last_error = f"Execution: {result.error}"
                continue

            result_text = self._format_result(result)
            explanation = self._llm.explain_result(request.question, sql, result_text)
            return TextToSQLResponse(
                question=request.question,
                sql=sql,
                result=result,
                explanation=explanation,
                attempts=attempts,
            )

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

    def _extract_sql(self, raw: str) -> str:
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            return "\n".join(lines).strip()
        return raw

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
