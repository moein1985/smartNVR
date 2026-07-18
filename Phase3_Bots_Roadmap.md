# Phase 3: Messaging Bots (Telegram + Bale) — Detailed Roadmap

## Objective

Integrate Telegram and Bale messaging bots that:
1. Respond to natural language queries (same Text-to-SQL use case)
2. Send automated event alerts when new detections occur
3. Support image/snapshot delivery from Frigate

---

## Prerequisites

- Phase 1 complete
- Phase 2 recommended (for shared API presenter logic)
- Telegram Bot Token from @BotFather
- Bale Bot Token from Bale platform

---

## Step 3.1: Add Bot Dependencies

**File: `frigate-intelligence/pyproject.toml` (update)**

Add to `dependencies`:
```toml
"python-telegram-bot>=21.0.0",
"httpx>=0.27.0",
```

---

## Step 3.2: Bot Presenter

**File: `src/frigate_intelligence/interface_adapters/presenters/bot_presenter.py`**

```python
from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import TextToSQLResponse

class BotPresenter:
    @staticmethod
    def to_markdown(response: TextToSQLResponse) -> str:
        lines = [
            f"**❓ سوال:** {response.question}",
            f"",
            f"**SQL:** `{response.sql}`",
            f"",
        ]
        if response.result.is_success and response.result.columns:
            header = " | ".join(response.result.columns[:5])
            lines.append(f"```\n{header}")
            for row in response.result.rows[:10]:
                lines.append(" | ".join(str(v)[:30] for v in row[:5]))
            lines.append(f"```\n_{response.result.row_count} رکورد_")
        elif response.result.error:
            lines.append(f"❌ خطا: {response.result.error}")

        lines.append(f"\n💡 {response.explanation}")
        return "\n".join(lines)

    @staticmethod
    def to_alert(event_dict: dict) -> str:
        from datetime import datetime
        dt = datetime.fromtimestamp(event_dict.get("start_time", 0)).strftime("%H:%M:%S")
        label = event_dict.get("label", "unknown")
        camera = event_dict.get("camera", "unknown")
        return f"🚨 **هشدار تشخیص**\n📋 اشیاء: {label}\n📷 دوربین: {camera}\n⏰ زمان: {dt}"
```

---

## Step 3.3: Telegram Notifier

**File: `src/frigate_intelligence/infrastructure/notifiers/telegram_notifier.py`**

```python
from telegram import Bot
from frigate_intelligence.domain.entities.notification import Notification

class TelegramNotifier:
    def __init__(self, bot_token: str, default_chat_id: str):
        self._bot = Bot(token=bot_token)
        self._default_chat_id = default_chat_id

    async def send(self, notification: Notification) -> bool:
        try:
            chat_id = notification.chat_id or self._default_chat_id
            if notification.image_path:
                with open(notification.image_path, "rb") as photo:
                    await self._bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=notification.message,
                        parse_mode="Markdown",
                    )
            else:
                await self._bot.send_message(
                    chat_id=chat_id,
                    text=notification.message,
                    parse_mode="Markdown",
                )
            return True
        except Exception:
            return False
```

---

## Step 3.4: Bale Notifier

**File: `src/frigate_intelligence/infrastructure/notifiers/bale_notifier.py`**

```python
import httpx
from frigate_intelligence.domain.entities.notification import Notification

class BaleNotifier:
    def __init__(self, bot_token: str, default_chat_id: str):
        self._token = bot_token
        self._default_chat_id = default_chat_id
        self._base_url = f"https://api.bale.ai/v1/bots/{bot_token}"

    async def send(self, notification: Notification) -> bool:
        try:
            chat_id = notification.chat_id or self._default_chat_id
            async with httpx.AsyncClient() as client:
                if notification.image_path:
                    # Upload photo then send
                    with open(notification.image_path, "rb") as photo:
                        files = {"photo": photo}
                        resp = await client.post(
                            f"{self._base_url}/sendPhoto",
                            data={"chat_id": chat_id, "caption": notification.message},
                            files=files,
                        )
                else:
                    resp = await client.post(
                        f"{self._base_url}/sendMessage",
                        json={"chat_id": chat_id, "text": notification.message},
                    )
            return resp.status_code == 200
        except Exception:
            return False
```

---

## Step 3.5: Bot Controller

**File: `src/frigate_intelligence/interface_adapters/controllers/bot_controller.py`**

```python
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from frigate_intelligence.use_cases.text_to_sql.text_to_sql_use_case import TextToSQLUseCase, TextToSQLRequest
from frigate_intelligence.interface_adapters.presenters.bot_presenter import BotPresenter

class TelegramBotController:
    def __init__(self, text_to_sql_use_case: TextToSQLUseCase, bot_token: str):
        self._use_case = text_to_sql_use_case
        self._token = bot_token
        self._presenter = BotPresenter()

    def create_app(self) -> Application:
        app = Application.builder().token(self._token).build()
        app.add_handler(CommandHandler("start", self._start))
        app.add_handler(CommandHandler("query", self._query_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        return app

    async def _start(self, update: Update, context):
        await update.message.reply_text(
            "سلام! من دستیار هوشمند دوربین‌های شما هستم.\n"
            "سوال خود را به زبان طبیعی بپرسید.\n"
            "مثال: آخرین رویدادهای شخصی که جلوی دوربین بود چه زمانی بود؟"
        )

    async def _query_command(self, update: Update, context):
        question = " ".join(context.args) if context.args else ""
        if not question:
            await update.message.reply_text("لطفاً سوال خود را بعد از /query بنویسید.")
            return
        await self._process_question(update, question)

    async def _handle_message(self, update: Update, context):
        question = update.message.text
        await self._process_question(update, question)

    async def _process_question(self, update: Update, question: str):
        await update.message.reply_text("در حال پردازش...")
        request = TextToSQLRequest(question=question)
        response = self._use_case.execute(request)
        markdown = self._presenter.to_markdown(response)
        await update.message.reply_text(markdown, parse_mode="Markdown")
```

---

## Step 3.6: Notification Use Case (Event Alerts)

**File: `src/frigate_intelligence/use_cases/send_notification/send_notification_use_case.py`**

```python
from dataclasses import dataclass
from frigate_intelligence.domain.entities.notification import Notification
from frigate_intelligence.domain.services.notifier_service import NotifierService

@dataclass
class SendNotificationRequest:
    message: str
    image_path: str | None = None
    chat_id: str | None = None
    event_id: str | None = None

@dataclass
class SendNotificationResponse:
    success: bool
    error: str | None = None

class SendNotificationUseCase:
    def __init__(self, notifier: NotifierService):
        self._notifier = notifier

    def execute(self, request: SendNotificationRequest) -> SendNotificationResponse:
        notification = Notification(
            message=request.message,
            image_path=request.image_path,
            chat_id=request.chat_id,
            event_id=request.event_id,
        )
        # Note: Telegram/Bale notifiers are async, caller must handle asyncio
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        success = loop.run_until_complete(self._notifier.send(notification))
        return SendNotificationResponse(success=success, error=None if success else "Send failed")
```

---

## Step 3.7: Frigate Webhook Integration

**File: `src/frigate_intelligence/infrastructure/api/routes/webhook_routes.py`**

```python
from fastapi import APIRouter, Request
from frigate_intelligence.use_cases.send_notification.send_notification_use_case import SendNotificationUseCase, SendNotificationRequest
from frigate_intelligence.interface_adapters.presenters.bot_presenter import BotPresenter

def create_webhook_router(notification_use_case: SendNotificationUseCase) -> APIRouter:
    router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

    @router.post("/frigate")
    async def frigate_webhook(request: Request):
        payload = await request.json()
        event_type = payload.get("type", "")
        event_data = payload.get("payload", {})

        if event_type == "new":
            alert_text = BotPresenter.to_alert(event_data)
            notification_req = SendNotificationRequest(
                message=alert_text,
                event_id=event_data.get("id"),
            )
            notification_use_case.execute(notification_req)

        return {"status": "ok"}

    return router
```

**Frigate config addition (`frigate-config.yml`):**
```yaml
notifications:
  - type: webhook
    url: http://127.0.0.1:8000/api/v1/webhooks/frigate
    events:
      - new
```

---

## Step 3.8: Bot Runner in Main

**File: `src/frigate_intelligence/main.py` (update)**

Add `bot` command:
```python
@app.command()
def bot(
    platform: str = typer.Option("telegram", help="Bot platform: telegram or bale"),
):
    """Start messaging bot."""
    settings = Settings()
    container = create_container(settings)
    if platform == "telegram":
        from frigate_intelligence.interface_adapters.controllers.bot_controller import TelegramBotController
        controller = TelegramBotController(container.text_to_sql_use_case, settings.telegram_bot_token)
        app_bot = controller.create_app()
        app_bot.run_polling()
    else:
        console.print("[red]Bale bot runner not yet implemented[/red]")
```

---

## Acceptance Criteria (Phase 3)

- [x] Telegram bot responds to `/start` with welcome message
- [x] Telegram bot responds to natural language questions with SQL + results + explanation
- [x] `/query <question>` command works
- [x] Free text messages are processed as questions
- [x] Bale notifier sends messages via Bale API
- [x] Frigate webhook triggers alert notifications
- [x] Alert messages include event label, camera, and time
- [x] Images/snapshots can be sent as attachments
- [x] Bot presenter formats output as Telegram Markdown

**Verification:**
```bash
uv run frigate-ai bot --platform telegram
# Then in Telegram: send message to bot
```
