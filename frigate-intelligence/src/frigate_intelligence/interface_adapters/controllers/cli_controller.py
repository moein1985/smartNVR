from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import (
    TextToSQLUseCase,
    TextToSQLRequest,
)
from frigate_intelligence.interface_adapters.presenters.cli_presenter import CLIPresenter


class CLIController:
    def __init__(self, text_to_sql_use_case: TextToSQLUseCase):
        self._use_case = text_to_sql_use_case
        self._presenter = CLIPresenter()

    def query(self, question: str) -> None:
        request = TextToSQLRequest(question=question)
        response = self._use_case.execute(request)
        self._presenter.show_response(response)
