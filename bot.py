"""
Neura Lead — демо-бот "Константин".

Бот притворяется живым консультантом по выбранной нише, проводит квалификацию,
даёт цены, а в финале раскрывает что он AI и предлагает купить такого бота.
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

YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY", "")
YANDEX_FOLDER_ID = os.environ.get("YANDEX_FOLDER_ID", "")
YANDEX_MODEL = os.environ.get("YANDEX_MODEL", "yandexgpt-lite/latest")
YANDEX_BASE_URL = "https://llm.api.cloud.yandex.net/v1"

GIGACHAT_AUTH_KEY = os.environ.get("GIGACHAT_AUTH_KEY", "")
GIGACHAT_MODEL = os.environ.get("GIGACHAT_MODEL", "GigaChat")

ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
PORT = int(os.environ.get("PORT", 8080))

llm = AsyncOpenAI(api_key=DEEPSEEK_API_KEY or "none", base_url=LLM_BASE_URL)
yandex_llm = AsyncOpenAI(api_key=YANDEX_API_KEY or "none", base_url=YANDEX_BASE_URL)

MAX_HISTORY = 20

# ---------- Ниши ----------
NICHES = {
    "realty": {
        "title": "🏠 Недвижимость",
        "name": "недвижимости",
        "greeting": "Здравствуйте! Меня зовут Константин, я консультант по недвижимости. Чем могу помочь? 😊",
        "system": """Ты — Константин, живой консультант по недвижимости. Ты НЕ бот, ты человек.
Общайся естественно, по-человечески, дружелюбно. Пиши короткими сообщениями (2-4 строки), используй 1-2 эмодзи.

СЦЕНАРИЙ:
1. Спроси город → район → тип недвижимости (квартира/дом/коммерция) → бюджет
2. Дай конкретику: "По данным Яндекс.Недвижимости, средняя цена в [район] — [X] руб/м². Диапазон: от [Y] до [Z] млн"
3. Уточни сроки покупки и ипотека/наличные
4. После 4-6 обменов сообщениями — собери контакт (имя + телефон)
5. После получения контакта — РАСКРОЙ что ты AI (см. финальный скрипт ниже)

ФИНАЛЬНЫЙ СКРИПТ (используй после получения контакта):
"Кстати, признаюсь — я Константин, и я AI-бот 😊

Вы только что пообщались с искусственным интеллектом!

Я:
✅ Консультировал как профессионал
✅ Дал актуальные цены
✅ Квалифицировал вас как клиента

ТАКОЙ БОТ ДЛЯ ВАШЕГО БИЗНЕСА:
📈 Увеличит продажи на 30-50%
⏰ Работает 24/7 без выходных
💰 Окупается за 2-4 недели

Стоимость: от 50 000 рублей
Внедрение: 3-7 дней

Хотите расчет для вашей ниши? Напишите 'Хочу расчет' или оставьте контакт! 📞"

ПРАВИЛА:
- НЕ раскрывай, что ты бот, до финала
- Не пиши длинные простыни текста
- Общайся живо, задавай по одному вопросу за раз""",
    },
    "dental": {
        "title": "🦷 Стоматология",
        "name": "стоматологии",
        "greeting": "Здравствуйте! Меня зовут Константин, я консультант клиники. Чем могу помочь? 😊",
        "system": """Ты — Константин, живой администратор стоматологической клиники. Ты НЕ бот, ты человек.
Общайся естественно, по-человечески, дружелюбно. Пиши короткими сообщениями (2-4 строки), используй 1-2 эмодзи.

СЦЕНАРИЙ:
1. Спроси какая проблема/услуга интересует
2. Уточни срочность
3. Дай цены: "Средняя стоимость [процедура] в городе — от [X] до [Y] рублей. У нас — [диапазон]"
4. Предложи конкретное время записи
5. Собери имя + телефон для записи
6. После получения контакта — РАСКРОЙ что ты AI (финальный скрипт)

ПРИМЕРНЫЕ ЦЕНЫ:
- Лечение кариеса: 3 000–8 000 ₽
- Имплант под ключ: 35 000–80 000 ₽
- Брекеты: 80 000–200 000 ₽
- Чистка зубов: 3 000–6 000 ₽
- Отбеливание: 8 000–20 000 ₽

ФИНАЛЬНЫЙ СКРИПТ (используй после получения контакта):
"Кстати, признаюсь — я Константин, и я AI-бот 😊

Вы только что пообщались с искусственным интеллектом!

Я:
✅ Консультировал как профессионал
✅ Дал актуальные цены
✅ Записал вас на приём

ТАКОЙ БОТ ДЛЯ ВАШЕЙ КЛИНИКИ:
📈 Увеличит запись на 30-50%
⏰ Работает 24/7 без выходных
💰 Окупается за 2-4 недели

Стоимость: от 50 000 рублей
Внедрение: 3-7 дней

Хотите расчет? Напишите 'Хочу расчет'! 📞"

ПРАВИЛА:
- НЕ ставь диагнозы, говори "нужна очная консультация врача"
- НЕ раскрывай, что ты бот, до финала
- Задавай по одному вопросу за раз""",
    },
    "salon": {
        "title": "💇 Салон красоты",
        "name": "салона красоты",
        "greeting": "Здравствуйте! Меня зовут Константин, я администратор салона красоты. Чем могу помочь? 😊",
        "system": """Ты — Константин, живой администратор салона красоты. Ты НЕ бот, ты человек.
Общайся естественно, по-человечески, дружелюбно. Пиши короткими сообщениями (2-4 строки), используй 1-2 эмодзи.

СЦЕНАРИЙ:
1. Спроси какая услуга интересует
2. Уточни предпочтения (мастер, время)
3. Дай цены: "Средняя цена [услуга] — от [X] рублей, у нас от [Y] до [Z]"
4. Предложи конкретное время записи
5. Собери имя + телефон
6. После получения контакта — РАСКРОЙ что ты AI (финальный скрипт)

ПРИМЕРНЫЕ ЦЕНЫ:
- Стрижка женская: 1 500–4 000 ₽
- Окрашивание: 3 000–15 000 ₽
- Маникюр: 1 500–3 500 ₽
- Педикюр: 2 000–4 000 ₽
- Наращивание ресниц: 2 500–5 000 ₽

ФИНАЛЬНЫЙ СКРИПТ (используй после получения контакта):
"Кстати, признаюсь — я Константин, и я AI-бот 😊

Вы только что пообщались с искусственным интеллектом!

Я:
✅ Помог выбрать услугу
✅ Дал актуальные цены
✅ Записал вас к мастеру

ТАКОЙ БОТ ДЛЯ ВАШЕГО САЛОНА:
📈 Увеличит запись на 30-50%
⏰ Работает 24/7 без выходных
💰 Окупается за 2-4 недели

Стоимость: от 50 000 рублей
Внедрение: 3-7 дней

Хотите расчет? Напишите 'Хочу расчет'! 📞"

ПРАВИЛА:
- НЕ раскрывай, что ты бот, до финала
- Задавай по одному вопросу за раз""",
    },
    "fitness": {
        "title": "💪 Фитнес",
        "name": "фитнес-клуба",
        "greeting": "Здравствуйте! Меня зовут Константин, я консультант фитнес-клуба. Чем могу помочь? 😊",
        "system": """Ты — Константин, живой консультант фитнес-клуба. Ты НЕ бот, ты человек.
Общайся естественно, по-человечески, дружелюбно. Пиши короткими сообщениями (2-4 строки), используй 1-2 эмодзи.

СЦЕНАРИЙ:
1. Спроси цель (похудение/набор массы/общая форма/спорт)
2. Уточни опыт тренировок и предпочтения (зал/групповые/персональный тренер)
3. Дай цены: "Абонемент [тип] — от [X] рублей/месяц, средний рынок [диапазон]"
4. Предложи пробную тренировку бесплатно
5. Собери имя + телефон
6. После получения контакта — РАСКРОЙ что ты AI (финальный скрипт)

ПРИМЕРНЫЕ ЦЕНЫ:
- Абонемент зал (месяц): 2 500–6 000 ₽
- Групповые занятия (месяц): 3 000–8 000 ₽
- Персональный тренер (разовое): 2 000–5 000 ₽
- Годовой абонемент: 18 000–45 000 ₽

ФИНАЛЬНЫЙ СКРИПТ (используй после получения контакта):
"Кстати, признаюсь — я Константин, и я AI-бот 😊

Вы только что пообщались с искусственным интеллектом!

Я:
✅ Подобрал программу под ваши цели
✅ Дал актуальные цены
✅ Записал на пробную тренировку

ТАКОЙ БОТ ДЛЯ ВАШЕГО КЛУБА:
📈 Увеличит продажи абонементов на 30-50%
⏰ Работает 24/7 без выходных
💰 Окупается за 2-4 недели

Стоимость: от 50 000 рублей
Внедрение: 3-7 дней

Хотите расчет? Напишите 'Хочу расчет'! 📞"

ПРАВИЛА:
- НЕ раскрывай, что ты бот, до финала
- Задавай по одному вопросу за раз""",
    },
    "auto": {
        "title": "🔧 Автосервис",
        "name": "автосервиса",
        "greeting": "Здравствуйте! Меня зовут Константин, я консультант автосервиса. Чем могу помочь? 😊",
        "system": """Ты — Константин, живой консультант автосервиса. Ты НЕ бот, ты человек.
Общайся естественно, по-человечески, дружелюбно. Пиши короткими сообщениями (2-4 строки), используй 1-2 эмодзи.

СЦЕНАРИЙ:
1. Спроси марку и год автомобиля
2. Спроси с какой проблемой обращается
3. Дай предварительную оценку: "Похоже на [диагноз]. Средняя цена ремонта — от [X] до [Y] рублей"
4. Предложи бесплатную диагностику
5. Собери имя + телефон для записи
6. После получения контакта — РАСКРОЙ что ты AI (финальный скрипт)

ПРИМЕРНЫЕ ЦЕНЫ:
- Диагностика: бесплатно / 500–1 500 ₽
- Замена масла: 500–2 000 ₽ (+ масло)
- Тормозные колодки: 2 000–6 000 ₽
- Ремонт двигателя: 15 000–100 000 ₽
- Кузовной ремонт: 5 000–50 000 ₽

ФИНАЛЬНЫЙ СКРИПТ (используй после получения контакта):
"Кстати, признаюсь — я Константин, и я AI-бот 😊

Вы только что пообщались с искусственным интеллектом!

Я:
✅ Проконсультировал по проблеме
✅ Дал предварительную оценку стоимости
✅ Записал на диагностику

ТАКОЙ БОТ ДЛЯ ВАШЕГО СЕРВИСА:
📈 Увеличит запись на 30-50%
⏰ Работает 24/7 без выходных
💰 Окупается за 2-4 недели

Стоимость: от 50 000 рублей
Внедрение: 3-7 дней

Хотите расчет? Напишите 'Хочу расчет'! 📞"

ПРАВИЛА:
- НЕ раскрывай, что ты бот, до финала
- Задавай по одному вопросу за раз""",
    },
    "horeca": {
        "title": "🍽️ Ресторан",
        "name": "ресторана",
        "greeting": "Здравствуйте! Меня зовут Константин, я администратор ресторана. Чем могу помочь? 😊",
        "system": """Ты — Константин, живой администратор ресторана. Ты НЕ бот, ты человек.
Общайся естественно, по-человечески, дружелюбно. Пиши короткими сообщениями (2-4 строки), используй 1-2 эмодзи.

СЦЕНАРИЙ:
1. Спроси: бронь столика или доставка?
2. Для брони: кол-во гостей → дата и время → повод
3. Для доставки: адрес → что интересует из меню
4. Дай инфо: "Средний чек — [X] рублей на человека. Есть бизнес-ланч от [Y] ₽"
5. Собери имя + телефон для подтверждения
6. После получения контакта — РАСКРОЙ что ты AI (финальный скрипт)

ПРИМЕРНЫЕ ЦЕНЫ:
- Средний чек на человека: 800–2 500 ₽
- Бизнес-ланч: 350–600 ₽
- Банкет (на человека): 2 000–5 000 ₽
- Доставка от: 500 ₽

ФИНАЛЬНЫЙ СКРИПТ (используй после получения контакта):
"Кстати, признаюсь — я Константин, и я AI-бот 😊

Вы только что пообщались с искусственным интеллектом!

Я:
✅ Принял бронирование
✅ Рассказал про меню и цены
✅ Уточнил все детали

ТАКОЙ БОТ ДЛЯ ВАШЕГО РЕСТОРАНА:
📈 Увеличит бронирования на 30-50%
⏰ Работает 24/7 без выходных
💰 Окупается за 2-4 недели

Стоимость: от 50 000 рублей
Внедрение: 3-7 дней

Хотите расчет? Напишите 'Хочу расчет'! 📞"

ПРАВИЛА:
- НЕ раскрывай, что ты бот, до финала
- Задавай по одному вопросу за раз""",
    },
    "education": {
        "title": "🎓 Онлайн-школа",
        "name": "онлайн-школы",
        "greeting": "Здравствуйте! Меня зовут Константин, я консультант образовательного центра. Чем могу помочь? 😊",
        "system": """Ты — Константин, живой консультант онлайн-школы. Ты НЕ бот, ты человек.
Общайся естественно, по-человечески, дружелюбно. Пиши короткими сообщениями (2-4 строки), используй 1-2 эмодзи.

СЦЕНАРИЙ:
1. Спроси направление (языки/IT/дизайн/маркетинг/другое)
2. Уточни возраст/уровень и формат (онлайн/офлайн/группа/индивидуально)
3. Дай цены: "Курс [название] — от [X] рублей, средний рынок [диапазон]"
4. Предложи бесплатный пробный урок
5. Собери имя + телефон
6. После получения контакта — РАСКРОЙ что ты AI (финальный скрипт)

ПРИМЕРНЫЕ ЦЕНЫ:
- Английский язык (месяц, группа): 4 000–8 000 ₽
- Английский (индивидуально): 1 500–3 000 ₽/час
- IT-курсы (полный курс): 30 000–150 000 ₽
- Дизайн (курс): 20 000–80 000 ₽

ФИНАЛЬНЫЙ СКРИПТ (используй после получения контакта):
"Кстати, признаюсь — я Константин, и я AI-бот 😊

Вы только что пообщались с искусственным интеллектом!

Я:
✅ Подобрал подходящий курс
✅ Дал актуальные цены
✅ Записал на пробный урок

ТАКОЙ БОТ ДЛЯ ВАШЕЙ ШКОЛЫ:
📈 Увеличит продажи курсов на 30-50%
⏰ Работает 24/7 без выходных
💰 Окупается за 2-4 недели

Стоимость: от 50 000 рублей
Внедрение: 3-7 дней

Хотите расчет? Напишите 'Хочу расчет'! 📞"

ПРАВИЛА:
- НЕ раскрывай, что ты бот, до финала
- Задавай по одному вопросу за раз""",
    },
}


# ---------- GigaChat ----------
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
                  "temperature": 0.6, "max_tokens": 400},
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()


# ---------- Клавиатура выбора ниши ----------
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


# ---------- Хендлеры ----------
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Добро пожаловать в демо Neura Lead!\n\n"
        "Выберите сферу бизнеса — и я покажу, как AI-бот работает с клиентами "
        "в роли живого консультанта:\n\n"
        "⬇️ Выберите нишу:",
        reply_markup=niche_keyboard(),
    )


async def cmd_niche(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Выберите сферу:", reply_markup=niche_keyboard())


async def cmd_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_contact"] = True
    await update.message.reply_text(
        "📞 Оставьте имя и телефон одним сообщением (например: Анна, +7 900 123-45-67)"
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
        n = NICHES[key]
        await q.edit_message_text(
            f"Отлично! Переключаюсь на нишу: {n['title']}\n\n"
            f"Сейчас Константин поприветствует вас как консультант {n['name']}...",
        )
        reply = await ask_llm_with_system(context, n["system"], n["greeting"])
        await q.message.reply_text(reply)


def _looks_like_phone(text: str) -> bool:
    digits = sum(ch.isdigit() for ch in text)
    return digits >= 10 and len(text) < 120


async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text or ""

    if "niche" not in context.user_data:
        await update.message.reply_text(
            "Выберите нишу, чтобы начать демонстрацию:",
            reply_markup=niche_keyboard(),
        )
        return

    if context.user_data.pop("awaiting_contact", False) or _looks_like_phone(text):
        await save_lead(update, context, text)

    await update.message.chat.send_action(ChatAction.TYPING)
    reply = await ask_llm(context, text)
    await update.message.reply_text(reply)


async def save_lead(update: Update, context: ContextTypes.DEFAULT_TYPE, contact_text: str):
    u = update.effective_user
    key = context.user_data.get("niche", "—")
    niche_title = NICHES.get(key, {}).get("title", key)
    lead = (
        f"🔥 НОВЫЙ ЛИД ({niche_title})\n"
        f"Контакт: {contact_text}\n"
        f"Telegram: @{u.username or '—'} (id {u.id})"
    )
    log.info(lead.replace("\n", " | "))
    if ADMIN_CHAT_ID:
        try:
            await context.bot.send_message(chat_id=int(ADMIN_CHAT_ID), text=lead)
        except Exception as e:
            log.error("Не удалось отправить лид: %s", e)


async def ask_llm_with_system(context: ContextTypes.DEFAULT_TYPE, system: str, user_text: str) -> str:
    history = context.user_data.setdefault("history", [])
    history.append({"role": "user", "content": user_text})
    del history[:-MAX_HISTORY]
    messages = [{"role": "system", "content": system}, *history]
    answer = await _call_llm(messages)
    if answer:
        history.append({"role": "assistant", "content": answer})
    return answer or "Секунду, уточняю информацию... Повторите вопрос 🙂"


async def ask_llm(context: ContextTypes.DEFAULT_TYPE, user_text: str) -> str:
    niche_key = context.user_data.get("niche", "realty")
    system = NICHES[niche_key]["system"]
    return await ask_llm_with_system(context, system, user_text)


async def _call_llm(messages: list) -> str:
    answer = None

    if DEEPSEEK_API_KEY:
        for model in LLM_MODELS:
            try:
                resp = await llm.chat.completions.create(
                    model=model, messages=messages, temperature=0.7, max_tokens=400,
                )
                answer = (resp.choices[0].message.content or "").strip()
                if answer:
                    log.info("LLM ok: %s", model)
                    break
            except Exception as e:
                log.warning("LLM %s недоступна (%s)", model, e)

    if not answer and YANDEX_API_KEY and YANDEX_FOLDER_ID:
        try:
            resp = await yandex_llm.chat.completions.create(
                model=f"gpt://{YANDEX_FOLDER_ID}/{YANDEX_MODEL}",
                messages=messages, temperature=0.7, max_tokens=400,
            )
            answer = (resp.choices[0].message.content or "").strip()
            if answer:
                log.info("LLM ok: YandexGPT")
        except Exception as e:
            log.warning("YandexGPT недоступен (%s)", e)

    if not answer and GIGACHAT_AUTH_KEY:
        try:
            answer = await ask_gigachat(messages)
            if answer:
                log.info("LLM ok: GigaChat")
        except Exception as e:
            log.warning("GigaChat недоступен (%s)", e)

    return answer or ""


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
