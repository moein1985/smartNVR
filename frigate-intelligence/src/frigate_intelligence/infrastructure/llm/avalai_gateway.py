import json
import logging
from typing import Generator

from openai import OpenAI

logger = logging.getLogger(__name__)


class AvalaiGateway:
    def __init__(self, api_key: str, base_url: str, model: str):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    def generate_sql(self, question: str, schema_context: str) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": schema_context,
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\n\nGenerate a SQLite SELECT query to answer this question.",
                },
            ],
            temperature=0.0,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()

    def classify_intent(self, question: str) -> dict:
        """Classify user intent as event_query or playback_query using JSON mode."""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an intent classifier for a surveillance NVR system. "
                        "Classify the user's question into one of these intents:\n"
                        "- 'event_query': Questions about detections, alerts, persons, objects, statistics, counts.\n"
                        "- 'playback_query': Requests to view video footage, watch recordings, see playback for a time range.\n\n"
                        "Respond as JSON: {\"intent\": \"event_query|playback_query\", \"camera\": \"cam1|null\", \"start_time\": \"ISO8601 or null\", \"end_time\": \"ISO8601 or null\"}"
                    ),
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            temperature=0.0,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        logger.info(f"[IntentClassification] question='{question}' -> {raw}")
        return json.loads(raw)

    def smart_query(self, question: str, schema_context: str) -> dict:
        """Unified LLM call: classify intent + generate SQL in a single response."""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": schema_context,
                },
                {
                    "role": "user",
                    "content": (
                        f"Question: {question}\n\n"
                        "Analyze this question and respond as JSON with these fields:\n"
                        "- \"intent\": \"event_query\" or \"playback_query\"\n"
                        "- \"sql\": SQLite SELECT query (for event_query) or empty string (for playback_query)\n"
                        "- \"camera\": camera name if mentioned, else null\n"
                        "- \"start_time\": ISO8601 start time if mentioned, else null\n"
                        "- \"end_time\": ISO8601 end time if mentioned, else null\n"
                        "- \"explanation\": brief natural language explanation"
                    ),
                },
            ],
            temperature=0.0,
            max_tokens=800,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content.strip()
        logger.info(f"[SmartQuery] question='{question}' -> {raw}")
        return json.loads(raw)

    def explain_result(
        self, question: str, sql: str, result_text: str
    ) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that explains database query results in natural language. Respond in the same language as the user's question.",
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\nSQL: {sql}\nResults:\n{result_text}\n\nExplain these results in natural language.",
                },
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()

    def explain_result_stream(
        self, question: str, sql: str, result_text: str
    ) -> Generator[str, None, None]:
        stream = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that explains database query results in natural language. Respond in the same language as the user's question.",
                },
                {
                    "role": "user",
                    "content": f"Question: {question}\nSQL: {sql}\nResults:\n{result_text}\n\nExplain these results in natural language.",
                },
            ],
            temperature=0.3,
            max_tokens=1000,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
