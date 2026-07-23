import datetime
import logging

from frigate_intelligence.domain.value_objects.prompt_context import PromptContext
from frigate_intelligence.interface_adapters.schemas.frigate_schema import (
    load_schema_context,
    get_frigate_zones,
    SAMPLE_QUERIES,
    SQL_RULES,
)

logger = logging.getLogger(__name__)


class PromptBuilder:
    @staticmethod
    def build(
        client_tz_info: dict | None = None,
        work_hours_start: str | None = None,
        work_hours_end: str | None = None,
    ) -> PromptContext:
        schema_text = load_schema_context(
            work_hours_start=work_hours_start,
            work_hours_end=work_hours_end,
        )
        zone_info = get_frigate_zones()
        schema_text = f"{schema_text}\n\n{zone_info}"
        time_context = PromptBuilder._build_time_context(client_tz_info)
        return PromptContext(
            schema_text=schema_text,
            sample_queries=SAMPLE_QUERIES,
            rules=SQL_RULES,
            time_context=time_context,
        )

    @staticmethod
    def _build_time_context(client_tz_info: dict | None) -> str:
        if not client_tz_info:
            return ""

        server_now = datetime.datetime.now(datetime.timezone.utc)
        server_ts = server_now.timestamp()

        offset_minutes = client_tz_info.get("offset_minutes")
        client_tz_name = client_tz_info.get("timezone") or "unknown"
        client_ts = client_tz_info.get("timestamp")

        if offset_minutes is None:
            return ""

        offset_delta = datetime.timedelta(minutes=offset_minutes)
        client_now = server_now + offset_delta

        client_date = client_now.strftime("%Y-%m-%d")
        client_time = client_now.strftime("%H:%M:%S")

        offset_hours = offset_minutes // 60
        offset_mins = abs(offset_minutes) % 60
        offset_str = f"{'+' if offset_minutes >= 0 else '-'}{abs(offset_hours):02d}:{offset_mins:02d}"

        start_of_client_today_utc = client_now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_client_today_ts = (start_of_client_today_utc - offset_delta).timestamp()

        context = (
            f"- Server UTC time: {server_now.strftime('%Y-%m-%d %H:%M:%S')} UTC (Unix: {server_ts:.0f})\n"
            f"- Client local time: {client_date} {client_time} (UTC{offset_str}, {client_tz_name})\n"
            f"- Offset: {offset_str} (client is {abs(offset_minutes)} minutes {'ahead' if offset_minutes > 0 else 'behind'})\n"
            f"- 'Today' for client = {client_date} ({client_tz_name})\n"
            f"- Start of client's today in UTC: {(start_of_client_today_utc - offset_delta).strftime('%Y-%m-%d %H:%M:%S')} UTC (Unix: {start_of_client_today_ts:.0f})\n"
            f"- When user says '9:00 AM', they mean 9:00 AM {client_tz_name} = {client_date} 09:00:00 {offset_str}\n"
            f"- To filter for 9:00 AM client time, compute: Unix timestamp = datetime('{client_date} 09:00:00', '{offset_str}') - strftime('%s', 'epoch')\n"
            f"- CRITICAL: SQLite `localtime` in this server equals UTC (server TZ is UTC). Do NOT use 'localtime' modifier for client timezone. Use explicit Unix timestamp ranges computed from the client offset."
        )

        if client_ts:
            skew = abs(client_ts - server_ts)
            if skew > 120:
                context += f"\n- WARNING: Client clock skew detected: {skew:.0f}s difference. Client timestamp: {client_ts:.0f}, Server timestamp: {server_ts:.0f}"

        logger.info(f"[TimeSync] Built time context: offset={offset_str}, client_date={client_date}")
        return context
