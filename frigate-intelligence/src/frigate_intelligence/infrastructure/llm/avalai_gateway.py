from openai import OpenAI


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
