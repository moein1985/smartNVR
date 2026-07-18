from frigate_intelligence.domain.value_objects.prompt_context import PromptContext
from frigate_intelligence.interface_adapters.schemas.frigate_schema import (
    load_schema_context,
    SAMPLE_QUERIES,
    SQL_RULES,
)


class PromptBuilder:
    @staticmethod
    def build() -> PromptContext:
        return PromptContext(
            schema_text=load_schema_context(),
            sample_queries=SAMPLE_QUERIES,
            rules=SQL_RULES,
        )
