import typer
from rich.console import Console

from frigate_intelligence.config.settings import Settings
from frigate_intelligence.config.dependencies import create_container
from frigate_intelligence.interface_adapters.controllers.cli_controller import (
    CLIController,
)

app = typer.Typer(help="Frigate Intelligence Platform CLI")
console = Console()


@app.command()
def query(
    question: str = typer.Argument(
        ..., help="Natural language question about camera events"
    ),
):
    """Ask a question about Frigate camera events in natural language."""
    settings = Settings()
    container = create_container(settings)
    controller = CLIController(container.text_to_sql_use_case)
    controller.query(question)


@app.command()
def interactive():
    """Start interactive chat mode."""
    settings = Settings()
    container = create_container(settings)
    controller = CLIController(container.text_to_sql_use_case)
    console.print("[bold green]Frigate Intelligence Interactive Mode[/bold green]")
    console.print("Type 'exit' to quit.\n")
    while True:
        question = typer.prompt("Question", default="")
        if question.lower() in ("exit", "quit", "q"):
            break
        if question:
            controller.query(question)
            console.print()


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host"),
    port: int = typer.Option(8000, help="Bind port"),
):
    """Start REST API server."""
    import uvicorn

    from frigate_intelligence.infrastructure.api.fastapi_app import create_app

    settings = Settings()
    container = create_container(settings)
    fastapi_app = create_app(container)
    console.print(
        f"[bold green]Starting Frigate Intelligence API on {host}:{port}[/bold green]"
    )
    uvicorn.run(fastapi_app, host=host, port=port)


@app.command()
def bot(
    platform: str = typer.Option("telegram", help="Bot platform: telegram or bale"),
):
    """Start messaging bot."""
    settings = Settings()
    container = create_container(settings)

    if platform == "telegram":
        if not settings.telegram_bot_token:
            console.print(
                "[red]Error: TELEGRAM_BOT_TOKEN not set in .env[/red]"
            )
            raise typer.Exit(1)
        from frigate_intelligence.interface_adapters.controllers.bot_controller import (
            TelegramBotController,
        )

        controller = TelegramBotController(
            container.text_to_sql_use_case, settings.telegram_bot_token
        )
        console.print("[bold green]Starting Telegram bot...[/bold green]")
        bot_app = controller.create_app()
        bot_app.run_polling()
    elif platform == "bale":
        console.print(
            "[yellow]Bale bot polling not yet implemented. "
            "Use webhook mode via REST API instead.[/yellow]"
        )
    else:
        console.print(f"[red]Unknown platform: {platform}[/red]")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
