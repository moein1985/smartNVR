from frigate_intelligence.domain.value_objects.prompt_context import PromptContext
from frigate_intelligence.interface_adapters.schemas.frigate_schema import (
    load_schema_context,
    get_frigate_zones,
    SAMPLE_QUERIES,
    SQL_RULES,
)


class PromptBuilder:
    @staticmethod
    def build() -> PromptContext:
        schema_text = load_schema_context()
        zone_info = get_frigate_zones()
        schema_text = f"{schema_text}\n\n{zone_info}"
        return PromptContext(
            schema_text=schema_text,
            sample_queries=SAMPLE_QUERIES,
            rules=SQL_RULES,
        )
