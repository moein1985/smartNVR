from dataclasses import dataclass

from frigate_intelligence.config.settings import Settings
from frigate_intelligence.infrastructure.database.frigate_sqlite_gateway import (
    FrigateSqliteGateway,
)
from frigate_intelligence.infrastructure.llm.avalai_gateway import AvalaiGateway
from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import (
    TextToSQLUseCase,
)
from frigate_intelligence.use_cases.correlate_pos.correlate_pos_use_case import (
    CorrelatePOSUseCase,
)
from frigate_intelligence.use_cases.analytics.analytics_use_case import (
    AnalyticsUseCase,
)
from frigate_intelligence.use_cases.send_notification.send_notification_use_case import (
    SendNotificationUseCase,
)


@dataclass
class Container:
    frigate_repo: FrigateSqliteGateway
    llm_service: AvalaiGateway
    text_to_sql_use_case: TextToSQLUseCase
    correlate_pos_use_case: CorrelatePOSUseCase
    analytics_use_case: AnalyticsUseCase
    notification_use_case: SendNotificationUseCase | None = None


def create_container(settings: Settings) -> Container:
    frigate_repo = FrigateSqliteGateway(db_path=settings.frigate_db_path)
    llm_service = AvalaiGateway(
        api_key=settings.avalai_api_key,
        base_url=settings.avalai_base_url,
        model=settings.llm_model,
    )
    text_to_sql = TextToSQLUseCase(
        frigate_repo=frigate_repo,
        llm_service=llm_service,
    )
    correlate_pos = CorrelatePOSUseCase(
        frigate_repo=frigate_repo,
        pos_repo=None,
    )
    analytics = AnalyticsUseCase(
        frigate_repo=frigate_repo,
    )
    return Container(
        frigate_repo=frigate_repo,
        llm_service=llm_service,
        text_to_sql_use_case=text_to_sql,
        correlate_pos_use_case=correlate_pos,
        analytics_use_case=analytics,
    )
