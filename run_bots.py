"""
Запуск демо-бота «Наш дом. Медиа» × NeuraLead сразу в Telegram и MAX — в ОДНОМ процессе.

Переменные окружения:
  BOT_TOKEN          — токен Telegram-бота (если нет — Telegram не запускается)
  ADMIN_CHAT_ID      — ваш Telegram ID: сюда приходят заявки и работает /leads
  MAX_BOT_TOKEN      — токен бота MAX (если нет — MAX не запускается)
  MAX_ADMIN_USER_ID  — ваш ID в MAX (необязательно; иначе заявки из MAX идут в Telegram)
  POLZA_API_KEY      — ключ Polza AI;  LLM_MODELS — модели через запятую (необязательно)
  DATA_DIR           — папка для базы (сделайте её постоянной на хостинге)
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime

from demo_brain import DemoBrain
from llm import transcribe
from storage import Storage

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
log = logging.getLogger("bots")
# httpx пишет в лог полные адреса запросов вместе с токеном бота — оставляем только предупреждения
logging.getLogger("httpx").setLevel(logging.WARNING)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "")
MAX_BOT_TOKEN = os.getenv("MAX_BOT_TOKEN", "")
MAX_ADMIN_USER_ID = os.getenv("MAX_ADMIN_USER_ID", "")
MAX_API = "https://platform-api.max.ru"

storage = Storage()
_tg_app = None
_max_client = None


async def notify(text: str) -> None:
    """Заявка менеджеру: в Telegram, если настроен, иначе в MAX."""
    if _tg_app and ADMIN_CHAT_ID:
        await _tg_app.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text=text)
    elif _max_client and MAX_ADMIN_USER_ID:
        await max_send(int(MAX_ADMIN_USER_ID), text)
    else:
        log.info("ЗАЯВКА (некуда отправить): %s", text.replace("\n", " | "))


brain = DemoBrain(storage, notify=notify)


# ================================================================== Telegram
def _tg_markup(buttons):
    if not buttons:
        return None
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    return InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=p) for t, p in row] for row in buttons])


def _tg_who(user) -> str:
    name = " ".join(filter(None, [user.first_name, user.last_name])) or "—"
    uname = f"@{user.username}" if user.username else f"id {user.id}"
    return f"Telegram: {name} ({uname})"


async def tg_on_text(update, context):
    msg = update.effective_message
    text = msg.text or ""
    if msg.voice:
        try:
            f = await msg.voice.get_file()
            text = await transcribe(bytes(await f.download_as_bytearray()))
        except Exception as e:
            log.error("Не удалось расшифровать голосовое: %s", e)
            await msg.reply_text("Не расслышал голосовое — напишите, пожалуйста, текстом.")
            return
    if not text:
        return
    from telegram.constants import ChatAction
    await msg.chat.send_action(ChatAction.TYPING)
    out = await brain.handle(f"tg:{msg.chat_id}", "telegram", text, _tg_who(update.effective_user))
    await msg.reply_text(out["text"], reply_markup=_tg_markup(out["buttons"]))


async def tg_on_button(update, context):
    q = update.callback_query
    await q.answer()
    out = await brain.handle(f"tg:{q.message.chat_id}", "telegram", q.data, _tg_who(q.from_user))
    await q.message.reply_text(out["text"], reply_markup=_tg_markup(out["buttons"]))


async def tg_on_leads(update, context):
    if str(update.effective_user.id) != str(ADMIN_CHAT_ID):
        return
    rows = storage.leads(10)
    if not rows:
        await update.effective_message.reply_text("Заявок пока нет.")
        return
    lines = []
    for r in rows:
        when = datetime.fromtimestamp(r["ts"]).strftime("%d.%m %H:%M")
        lines.append(f"#{r['id']} {when} · {r['channel']} · {r['name'] or '—'} {r['phone'] or ''}\n   {r['interest'] or ''} {r['summary'][:120]}")
    await update.effective_message.reply_text("Последние заявки:\n\n" + "\n".join(lines))


async def run_telegram():
    global _tg_app
    from telegram.ext import Application, CallbackQueryHandler, CommandHandler, MessageHandler, filters
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("leads", tg_on_leads))
    app.add_handler(CallbackQueryHandler(tg_on_button))
    app.add_handler(MessageHandler((filters.TEXT | filters.VOICE), tg_on_text))  # /start тоже сюда
    _tg_app = app
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    log.info("Telegram-бот запущен")
    await asyncio.Event().wait()


# ================================================================== MAX
def _max_buttons(buttons):
    if not buttons:
        return None
    return [{"type": "inline_keyboard", "payload": {"buttons": [
        [{"type": "callback", "text": t, "payload": p} for t, p in row] for row in buttons]}}]


async def max_send(user_id: int, text: str, buttons=None) -> None:
    body: dict = {"text": text}
    att = _max_buttons(buttons)
    if att:
        body["attachments"] = att
    r = await _max_client.post(f"{MAX_API}/messages", params={"user_id": user_id}, json=body,
                               headers={"Authorization": MAX_BOT_TOKEN}, timeout=20)
    r.raise_for_status()


async def max_handle(update: dict) -> None:
    kind = update.get("update_type")
    if kind == "message_created":
        msg = update.get("message") or {}
        user = msg.get("sender") or {}
        uid, text = user.get("user_id"), ((msg.get("body") or {}).get("text") or "").strip()
    elif kind == "message_callback":
        cb = update.get("callback") or {}
        user = cb.get("user") or {}
        uid, text = user.get("user_id"), cb.get("payload") or ""
        try:
            await _max_client.post(f"{MAX_API}/answers", params={"callback_id": cb.get("callback_id")},
                                   json={"notification": "✓"}, headers={"Authorization": MAX_BOT_TOKEN}, timeout=10)
        except Exception as e:
            log.warning("MAX: не ответил на кнопку: %s", e)
    elif kind == "bot_started":
        user = update.get("user") or {}
        uid, text = user.get("user_id"), "/start"
    else:
        return
    if not uid or not text or user.get("is_bot"):
        return
    who = f"MAX: {user.get('name') or '—'} (id {uid})"
    out = await brain.handle(f"max:{uid}", "max", text, who)
    await max_send(int(uid), out["text"], out["buttons"])


async def run_max():
    global _max_client
    import httpx
    _max_client = httpx.AsyncClient()
    marker = None
    log.info("MAX-бот запущен")
    while True:
        try:
            params = {"timeout": 30, "limit": 100}
            if marker is not None:
                params["marker"] = marker
            r = await _max_client.get(f"{MAX_API}/updates", params=params,
                                      headers={"Authorization": MAX_BOT_TOKEN}, timeout=40)
            r.raise_for_status()
            data = r.json()
            marker = data.get("marker", marker)
            for upd in data.get("updates", []):
                try:
                    await max_handle(upd)
                except Exception as e:
                    log.error("MAX: ошибка обработки: %s", e)
        except Exception as e:
            if "Timeout" not in type(e).__name__:
                log.error("MAX: ошибка получения сообщений: %s", e)
                await asyncio.sleep(5)


async def main():
    tasks = []
    if BOT_TOKEN:
        tasks.append(run_telegram())
    if MAX_BOT_TOKEN:
        tasks.append(run_max())
    if not tasks:
        raise SystemExit("Нет BOT_TOKEN и MAX_BOT_TOKEN — запускать нечего.")
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
