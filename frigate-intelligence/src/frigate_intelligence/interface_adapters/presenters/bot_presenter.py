from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import (
    TextToSQLResponse,
)


class BotPresenter:
    @staticmethod
    def to_markdown(response: TextToSQLResponse) -> str:
        lines = [
            f"**Question:** {response.question}",
            "",
            f"**SQL:** `{response.sql}`",
            "",
        ]
        if response.result.is_success and response.result.columns:
            header = " | ".join(response.result.columns[:5])
            lines.append(f"```\n{header}")
            for row in response.result.rows[:10]:
                lines.append(" | ".join(str(v)[:30] for v in row[:5]))
            lines.append(f"```\n_{response.result.row_count} rows_")
        elif response.result.error:
            lines.append(f"Error: {response.result.error}")

        lines.append(f"\n{response.explanation}")
        return "\n".join(lines)

    @staticmethod
    def to_alert(event_dict: dict) -> str:
        from datetime import datetime

        dt = datetime.fromtimestamp(event_dict.get("start_time", 0)).strftime(
            "%H:%M:%S"
        )
        label = event_dict.get("label", "unknown")
        camera = event_dict.get("camera", "unknown")
        return (
            f"**Detection Alert**\n"
            f"Object: {label}\n"
            f"Camera: {camera}\n"
            f"Time: {dt}"
        )
