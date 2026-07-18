from dataclasses import dataclass


@dataclass(frozen=True)
class PromptContext:
    schema_text: str
    sample_queries: str
    rules: str

    def as_system_prompt(self) -> str:
        return f"""You are a SQL expert assistant for a Frigate NVR surveillance system database.

## Database Schema
{self.schema_text}

## Example Queries
{self.sample_queries}

## Rules
{self.rules}

Generate ONLY a valid SQLite SELECT query. No explanations, no markdown fences.
The query must be safe (SELECT only, no modifications)."""
