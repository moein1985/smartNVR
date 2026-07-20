from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import (
    TextToSQLUseCase,
    TextToSQLRequest,
)
from frigate_intelligence.interface_adapters.presenters.bot_presenter import (
    BotPresenter,
)


class TelegramBotController:
    def __init__(self, text_to_sql_use_case: TextToSQLUseCase, bot_token: str):
        self._use_case = text_to_sql_use_case
        self._token = bot_token
        self._presenter = BotPresenter()

    def create_app(self):
        from telegram.ext import (
            Application,
            CommandHandler,
            MessageHandler,
            filters,
        )

        app = Application.builder().token(self._token).build()
        app.add_handler(CommandHandler("start", self._start))
        app.add_handler(CommandHandler("query", self._query_command))
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
        )
        return app

    async def _start(self, update, context):
        await update.message.reply_text(
            "Hello! I am your smart camera assistant.\n"
            "Ask me questions about camera events in natural language.\n"
            "Example: When was the last person detected?"
        )

    async def _query_command(self, update, context):
        question = " ".join(context.args) if context.args else ""
        if not question:
            await update.message.reply_text(
                "Please provide a question after /query"
            )
            return
        await self._process_question(update, question)

    async def _handle_message(self, update, context):
        question = update.message.text
        await self._process_question(update, question)

    async def _process_question(self, update, question):
        await update.message.reply_text("Processing...")
        request = TextToSQLRequest(question=question)
        response = self._use_case.execute(request)
        markdown = self._presenter.to_markdown(response)
        await update.message.reply_text(markdown, parse_mode="Markdown")
