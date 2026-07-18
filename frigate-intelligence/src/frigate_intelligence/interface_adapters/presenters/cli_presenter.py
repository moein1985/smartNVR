from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import (
    TextToSQLResponse,
)


class CLIPresenter:
    def __init__(self):
        self._console = Console()

    def show_response(self, response: TextToSQLResponse) -> None:
        self._console.print(
            Panel(
                f"[bold cyan]Question:[/bold cyan] {response.question}",
                title="Query",
            )
        )
        self._console.print(f"[dim]SQL (attempts: {response.attempts}):[/dim]")
        self._console.print(
            Panel(response.sql, title="Generated SQL", border_style="green")
        )

        if response.result.is_success and response.result.columns:
            table = Table(show_header=True, header_style="bold magenta")
            for col in response.result.columns:
                table.add_column(col)
            for row in response.result.rows[:50]:
                table.add_row(*[str(v)[:50] for v in row])
            self._console.print(table)
            self._console.print(f"[dim]{response.result.row_count} rows total[/dim]")
        elif response.result.error:
            self._console.print(f"[red]Error: {response.result.error}[/red]")

        self._console.print(
            Panel(
                response.explanation,
                title="Explanation",
                border_style="blue",
            )
        )

    def show_error(self, message: str) -> None:
        self._console.print(f"[red]Error: {message}[/red]")
