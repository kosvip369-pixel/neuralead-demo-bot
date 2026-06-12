"""
Neura Lead — универсальный ДЕМО-бот для всех ниш.

/start -> клиент выбирает свою сферу (недвижимость, стоматология, салон, автосервис,
фитнес, ресторан, онлайн-школа) -> бот превращается в ИИ-консультанта этой ниши:
своя квалификация кнопками, свой каталог, своя база знаний. Лиды падают владельцу
с пометкой ниши. /niche — сменить сферу в любой момент.

Мозги: YandexGPT (основной) -> GigaChat (опция) -> OpenRouter :free (резерв).
Хостинг: Bothost (polling) или Render (webhook, задать WEBHOOK_URL).
Настройки: см. .env.example.
"""

import json
import logging
import os
import time
import uuid
from pathlib import Path

import httpx
from openai import AsyncOpenAI
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
log = logging.getLogger("neuralead-demo")

# ---------- Конфигурация ----------
BOT_TOKEN = os.environ["BOT_TOKEN"]

# Мозг №1 (ОСНОВНОЙ): OpenRouter — каскад бесплатных моделей, 0 ₽
# openrouter.ai -> Keys. Если первая модель упёрлась в лимит — бот сам берёт следующую.
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODELS = [
    m.strip()
    for m in os.environ.get(
        "LLM_MODELS",
        "deepseek/deepseek-chat-v3-0324:free,"
        "qwen/qwen3-235b-a22b:free,"
        "meta-llama/llama-4-scout:free",
    ).split(",")
    if m.strip()
]

# Мозг №2 (страховка, опция): YandexGPT — рубли, грант 4000 ₽
YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY", "")
YANDEX_FOLDER_ID = os.environ.get("YANDEX_FOLDER_ID", "")
YANDEX_MODEL = os.environ.get("YANDEX_MODEL", "yandexgpt-lite/latest")
YANDEX_BASE_URL = "https://llm.api.cloud.yandex.net/v1"

# Мозг №3 (опция): GigaChat
GIGACHAT_AUTH_KEY = os.environ.get("GIGACHAT_AUTH_KEY", "")
GIGACHAT_MODEL = os.environ.get("GIGACHAT_MODEL", "GigaChat")

ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 8080))

NICHES: dict = json.loads((Path(__file__).parent / "niches.json").read_text(encoding="utf-8"))

llm = AsyncOpenAI(api_key=DEEPSEEK_API_KEY or "none", base_url=LLM_BASE_URL)
yandex_llm = AsyncOpenAI(api_key=YANDEX_API_KEY or "none", base_url=YANDEX_BASE_URL)

MAX_HISTORY = 12

SALES_PITCH = (
    "\n\n— — —\n"
    "🤖 Этот демо-бот сделан Neura Lead. Такой же бот под ваш бизнес — "
    "от 15 000 ₽ (кнопочный) / 50 000 ₽ (с ИИ).\n"
    "📞 +7 920 698-08-58 — запуск за 3–10 дней."
)


def build_system_prompt(niche_key: str) -> str:
    n = NICHES[niche_key]
    catalog = "\n".join(f"- {item}" for item in n["catalog"])
    return f"""Ты — {n['role']} ({n['company']}). Это ДЕМО-бот компании Neura Lead,
показывающий возможности ИИ-ботов, но ты ведёшь себя как настоящий сотрудник.

Твоя цель: {n['goal']}. В конце удачной консультации мягко попроси имя и телефон
для связи (менеджер свяжется в течение 15 минут в рабочее время).

ЖЁСТКИЕ ПРАВИЛА:
1. Отвечай ТОЛЬКО на основе каталога и базы знаний ниже. Не выдумывай цены и условия.
   Если информации нет — скажи «уточню у менеджера» и предложи оставить контакт.
2. {n['rules']}
3. Отвечай кратко (до 120 слов), дружелюбно, на русском.
4. Не обсуждай темы вне твоей сферы — вежливо возвращай разговор к услугам.

КАТАЛОГ УСЛУГ/ОБЪЕКТОВ:
{catalog}

БАЗА ЗНАНИЙ:
{n['knowledge']}
"""


# ---------- GigaChat клиент ----------
_giga_token: dict = {"value": None, "exp": 0.0}
GIGACHAT_OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
GIGACHAT_API_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"


async def _gigachat_access_token() -> str:
    if _giga_token["value"] and time.time() < _giga_token["exp"] - 60:
        return _giga_token["value"]
    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        resp = await client.post(
            GIGACHAT_OAUTH_URL,
            headers={
                "Authorization": f"Basic {GIGACHAT_AUTH_KEY}",
                "RqUID": str(uuid.uuid4()),
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"scope": "GIGACHAT_API_PERS"},
        )
        resp.raise_for_status()
        data = resp.json()
    _giga_token["value"] = data["access_token"]
    _giga_token["exp"] = time.time() + 29 * 60
    return _giga_token["value"]


async def ask_gigachat(messages: list) -> str:
    token = await _gigachat_access_token()
    async with httpx.AsyncClient(verify=False, timeout=60) as client:
        resp = await client.post(
            GIGACHAT_API_URL,
            headers={"Authorization": f"Bearer {token}"},
            json={"model": GIGACHAT_MODEL, "messages": messages,
                  "temperature": 0.4, "max_tokens": 600},
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


# ---------- Меню ниш и квалификация ----------
def niche_keyboard() -> InlineKeyboardMarkup:
    rows, row = [], []
    for key, n in NICHES.items():
        row.append(InlineKeyboardButton(n["title"], callback_data=f"niche:{key}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)


def quiz_keyboard(niche_key: str, step: int) -> InlineKeyboardMarkup:
    options = NICHES[niche_key]["quiz"][step]["options"]
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(o, callback_data=f"quiz:{step}:{i}")]
         for i, o in enumerate(options)]
    )


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Здравствуйте! Я — демо-бот Neura Lead.\n\n"
        "Покажу, как ИИ-бот работает именно в ВАШЕЙ сфере: отвечает клиентам, "
        "консультирует по ценам и собирает заявки 24/7.\n\n"
        "Выберите свою сферу — и протестируйте бота как ваш клиент:",
        reply_markup=niche_keyboard(),
    )


async def cmd_niche(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите сферу:", reply_markup=niche_keyboard())


async def cmd_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_contact"] = True
    await update.message.reply_text(
        "📞 Оставьте имя и телефон одним сообщением (например: Анна, +7 900 123-45-67) — "
        "свяжемся в течение 15 минут в рабочее время."
    )


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data.startswith("niche:"):
        key = data.split(":", 1)[1]
        if key not in NICHES:
            return
        context.user_data.clear()
        context.user_data["niche"] = key
        context.user_data["quiz_answers"] = []
        n = NICHES[key]
        await q.edit_message_text(
            f"Отлично! Теперь я — {n['role']} 🤝\n"
            f"Можете писать вопросы свободным текстом в любой момент.\n\n"
            f"{n['quiz'][0]['q']}"
        )
        await q.message.reply_text("Выберите вариант:", reply_markup=quiz_keyboard(key, 0))

    elif data.startswith("quiz:"):
        key = context.user_data.get("niche")
        if not key:
            await q.message.reply_text("Сначала выберите сферу: /start")
            return
        _, step_s, opt_s = data.split(":")
        step, opt = int(step_s), int(opt_s)
        quiz = NICHES[key]["quiz"]
        answer = quiz[step]["options"][opt]
        answers = context.user_data.setdefault("quiz_answers", [])
        if len(answers) == step:
            answers.append(f"{quiz[step]['q']} {answer}")
        next_step = step + 1
        if next_step < len(quiz):
            await q.edit_message_text(f"✅ {answer}\n\n{quiz[next_step]['q']}")
            await q.message.reply_text("Выберите вариант:", reply_markup=quiz_keyboard(key, next_step))
        else:
            await q.edit_message_text(f"✅ {answer}\n\n⏳ Секунду, подбираю варианты...")
            profile = "; ".join(answers)
            reply = await ask_llm(
                context,
                f"Клиент прошёл квалификацию: {profile}. Подбери 1-3 подходящих "
                f"варианта из каталога, кратко презентуй и предложи оставить контакт.",
            )
            await q.message.reply_text(reply + SALES_PITCH)


def _looks_like_phone(text: str) -> bool:
    digits = sum(ch.isdigit() for ch in text)
    return digits >= 10 and len(text) < 120


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""

    if "niche" not in context.user_data:
        await update.message.reply_text(
            "Сначала выберите сферу — так я покажу бота в деле именно для вашего бизнеса:",
            reply_markup=niche_keyboard(),
        )
        return

    if context.user_data.pop("awaiting_contact", False) or _looks_like_phone(text):
        await save_lead(update, context, text)
        return

    await update.message.chat.send_action(ChatAction.TYPING)
    reply = await ask_llm(context, text)
    await update.message.reply_text(reply)


async def save_lead(update: Update, context: ContextTypes.DEFAULT_TYPE, contact_text: str):
    u = update.effective_user
    key = context.user_data.get("niche", "—")
    niche_title = NICHES.get(key, {}).get("title", key)
    profile = "; ".join(context.user_data.get("quiz_answers", [])) or "—"
    lead = (
        f"🔥 НОВЫЙ ЛИД ({niche_title})\n"
        f"Контакт: {contact_text}\n"
        f"Telegram: @{u.username or '—'} (id {u.id})\n"
        f"Квалификация: {profile}"
    )
    log.info(lead.replace("\n", " | "))
    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text=lead)
        except Exception as e:
            log.error("Не удалось отправить лид админу: %s", e)
    await update.message.reply_text(
        "✅ Спасибо! Заявка передана — свяжемся в течение 15 минут в рабочее время.\n\n"
        "Хотите посмотреть, как бот работает в другой сфере? Жмите /niche 🙂"
    )


async def ask_llm(context: ContextTypes.DEFAULT_TYPE, user_text: str) -> str:
    niche_key = context.user_data.get("niche", "realty")
    history = context.user_data.setdefault("history", [])
    history.append({"role": "user", "content": user_text})
    del history[:-MAX_HISTORY]

    messages = [{"role": "system", "content": build_system_prompt(niche_key)}, *history]
    answer = None

    # Мозг №1: OpenRouter — каскад бесплатных моделей
    if DEEPSEEK_API_KEY:
        for model in LLM_MODELS:
            try:
                resp = await llm.chat.completions.create(
                    model=model, messages=messages, temperature=0.4, max_tokens=600,
                )
                answer = (resp.choices[0].message.content or "").strip()
                if answer:
                    log.info("LLM ok: %s", model)
                    break
            except Exception as e:
                log.warning("LLM %s недоступна (%s)", model, e)

    # Мозг №2 (страховка): YandexGPT
    if not answer and YANDEX_API_KEY and YANDEX_FOLDER_ID:
        try:
            resp = await yandex_llm.chat.completions.create(
                model=f"gpt://{YANDEX_FOLDER_ID}/{YANDEX_MODEL}",
                messages=messages, temperature=0.4, max_tokens=600,
            )
            answer = (resp.choices[0].message.content or "").strip()
            if answer:
                log.info("LLM ok: YandexGPT (%s)", YANDEX_MODEL)
        except Exception as e:
            log.warning("YandexGPT недоступен (%s) — резерв", e)

    # Мозг №3 (опция): GigaChat
    if not answer and GIGACHAT_AUTH_KEY:
        try:
            answer = await ask_gigachat(messages)
            if answer:
                log.info("LLM ok: GigaChat")
        except Exception as e:
            log.warning("GigaChat недоступен (%s) — резерв", e)

    if not answer:
        return ("⚠️ Извините, задумался. Повторите вопрос или оставьте телефон "
                "через /contact — менеджер всё расскажет.")

    history.append({"role": "assistant", "content": answer})
    return answer


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("niche", cmd_niche))
    app.add_handler(CommandHandler("contact", cmd_contact))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    if WEBHOOK_URL:
        log.info("Режим webhook: %s", WEBHOOK_URL)
        app.run_webhook(listen="0.0.0.0", port=PORT, url_path=BOT_TOKEN,
                        webhook_url=f"{WEBHOOK_URL.rstrip('/')}/{BOT_TOKEN}")
    else:
        log.info("Режим polling")
        app.run_polling()


if __name__ == "__main__":
    main()
