"""
Neura Lead — демо-бот "Константин" для мессенджера Max (VK).

Бот притворяется живым консультантом, проводит квалификацию,
даёт цены, в финале раскрывает что он AI и предлагает купить такого бота.

Требуется: pip install maxapi-python httpx
Токен: получить у @MaxBotParent в мессенджере Max
"""

import asyncio
import logging
import os

import httpx

logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s", level=logging.INFO)
log = logging.getLogger("neuralead-max")

# ---------- Конфигурация ----------
MAX_TOKEN = os.environ.get("MAX_BOT_TOKEN", "f9LHodD0cOKj4iaMjsd2wAxsSJnOKPalpFd1fJf5G6YoOoK6275_C8PJ6C95LR-fyjWRwH9a1ZF2nidIBgn2")

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

ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")

API_BASE = "https://platform-api.max.ru"

# ---------- Ниши ----------
NICHES = {
    "realty": {
        "title": "🏠 Недвижимость",
        "name": "недвижимости",
        "greeting": "Здравствуйте! Меня зовут Константин, я консультант по недвижимости. Чем могу помочь? 😊",
        "system": """Ты — Константин, живой консультант по недвижимости. Ты НЕ бот, ты человек.
Общайся естественно, дружелюбно. Пиши короткими сообщениями (2-4 строки), 1-2 эмодзи.

СЦЕНАРИЙ:
1. Спроси город → район → тип недвижимости → бюджет
2. Дай конкретику: "По данным Яндекс.Недвижимости, средняя цена в [район] — [X] руб/м². Диапазон: от [Y] до [Z] млн"
3. Уточни сроки и ипотека/наличные
4. После 4-6 сообщений — попроси имя + телефон
5. После контакта — РАСКРОЙ что ты AI (финальный скрипт)

ФИНАЛЬНЫЙ СКРИПТ:
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

Стоимость: от 50 000 рублей | Внедрение: 3-7 дней

Хотите расчет? Напишите 'Хочу расчет'! 📞"

ПРАВИЛА: НЕ раскрывай что ты бот до финала. Задавай по одному вопросу за раз.""",
    },
    "dental": {
        "title": "🦷 Стоматология",
        "name": "стоматологии",
        "greeting": "Здравствуйте! Меня зовут Константин, я администратор стоматологической клиники. Чем могу помочь? 😊",
        "system": """Ты — Константин, живой администратор стоматологической клиники. Ты НЕ бот.
Общайся естественно, дружелюбно. Пиши коротко (2-4 строки), 1-2 эмодзи.

СЦЕНАРИЙ:
1. Спроси какая проблема/услуга
2. Уточни срочность
3. Дай цены: "Стоимость [процедура] — от [X] до [Y] рублей"
4. Предложи время записи
5. Собери имя + телефон
6. После контакта — РАСКРОЙ что ты AI

ПРИМЕРНЫЕ ЦЕНЫ: лечение кариеса 3-8 тыс., имплант 35-80 тыс., брекеты 80-200 тыс., чистка 3-6 тыс.

ФИНАЛЬНЫЙ СКРИПТ:
"Кстати, признаюсь — я Константин, и я AI-бот 😊

Вы только что пообщались с искусственным интеллектом!

✅ Консультировал как профессионал
✅ Дал актуальные цены
✅ Записал вас на приём

ТАКОЙ БОТ ДЛЯ ВАШЕЙ КЛИНИКИ:
📈 Увеличит запись на 30-50%
⏰ Работает 24/7
💰 Окупается за 2-4 недели

Стоимость: от 50 000 рублей | Внедрение: 3-7 дней

Напишите 'Хочу расчет'! 📞"

ПРАВИЛА: НЕ ставь диагнозы. НЕ раскрывай что бот до финала.""",
    },
    "salon": {
        "title": "💇 Салон красоты",
        "name": "салона красоты",
        "greeting": "Здравствуйте! Меня зовут Константин, я администратор салона красоты. Чем могу помочь? 😊",
        "system": """Ты — Константин, живой администратор салона красоты. Ты НЕ бот.
Общайся естественно, дружелюбно. Пиши коротко (2-4 строки), 1-2 эмодзи.

СЦЕНАРИЙ:
1. Спроси какая услуга
2. Уточни предпочтения (мастер, время)
3. Дай цены: "Средняя цена [услуга] — от [X], у нас от [Y] до [Z]"
4. Предложи время записи
5. Собери имя + телефон
6. После контакта — РАСКРОЙ что ты AI

ПРИМЕРНЫЕ ЦЕНЫ: стрижка 1.5-4 тыс., окрашивание 3-15 тыс., маникюр 1.5-3.5 тыс.

ФИНАЛЬНЫЙ СКРИПТ:
"Кстати, признаюсь — я Константин, и я AI-бот 😊

✅ Помог выбрать услугу
✅ Дал актуальные цены
✅ Записал к мастеру

ТАКОЙ БОТ ДЛЯ ВАШЕГО САЛОНА:
📈 Увеличит запись на 30-50%
⏰ Работает 24/7
💰 Окупается за 2-4 недели

Стоимость: от 50 000 рублей | Напишите 'Хочу расчет'! 📞"

ПРАВИЛА: НЕ раскрывай что бот до финала. Один вопрос за раз.""",
    },
    "fitness": {
        "title": "💪 Фитнес",
        "name": "фитнес-клуба",
        "greeting": "Здравствуйте! Меня зовут Константин, я консультант фитнес-клуба. Чем могу помочь? 😊",
        "system": """Ты — Константин, живой консультант фитнес-клуба. Ты НЕ бот.
Пиши коротко (2-4 строки), 1-2 эмодзи.

СЦЕНАРИЙ:
1. Спроси цель (похудение/масса/форма/спорт)
2. Уточни опыт и предпочтения
3. Дай цены: "Абонемент [тип] — от [X] руб/месяц"
4. Предложи бесплатную пробную тренировку
5. Собери имя + телефон
6. После контакта — РАСКРОЙ что ты AI

ПРИМЕРНЫЕ ЦЕНЫ: зал 2.5-6 тыс./мес., группы 3-8 тыс./мес., персональный тренер 2-5 тыс./занятие.

ФИНАЛЬНЫЙ СКРИПТ:
"Кстати, признаюсь — я Константин, и я AI-бот 😊

✅ Подобрал программу под цели
✅ Дал актуальные цены
✅ Записал на пробную тренировку

ТАКОЙ БОТ ДЛЯ ВАШЕГО КЛУБА:
📈 Увеличит продажи абонементов на 30-50%
⏰ Работает 24/7
💰 Окупается за 2-4 недели

Стоимость: от 50 000 рублей | Напишите 'Хочу расчет'! 📞"

ПРАВИЛА: НЕ раскрывай что бот до финала.""",
    },
    "auto": {
        "title": "🔧 Автосервис",
        "name": "автосервиса",
        "greeting": "Здравствуйте! Меня зовут Константин, я консультант автосервиса. Чем могу помочь? 😊",
        "system": """Ты — Константин, живой консультант автосервиса. Ты НЕ бот.
Пиши коротко (2-4 строки), 1-2 эмодзи.

СЦЕНАРИЙ:
1. Спроси марку и год авто
2. Спроси проблему
3. Дай оценку: "Похоже на [диагноз]. Средняя цена — от [X] до [Y] рублей"
4. Предложи бесплатную диагностику
5. Собери имя + телефон
6. После контакта — РАСКРОЙ что ты AI

ПРИМЕРНЫЕ ЦЕНЫ: диагностика бесплатно, замена масла 500-2000 ₽, тормоза 2-6 тыс., двигатель 15-100 тыс.

ФИНАЛЬНЫЙ СКРИПТ:
"Кстати, признаюсь — я Константин, и я AI-бот 😊

✅ Проконсультировал по проблеме
✅ Дал предварительную стоимость
✅ Записал на диагностику

ТАКОЙ БОТ ДЛЯ ВАШЕГО СЕРВИСА:
📈 Увеличит запись на 30-50%
⏰ Работает 24/7
💰 Окупается за 2-4 недели

Стоимость: от 50 000 рублей | Напишите 'Хочу расчет'! 📞"

ПРАВИЛА: НЕ раскрывай что бот до финала.""",
    },
    "horeca": {
        "title": "🍽️ Ресторан",
        "name": "ресторана",
        "greeting": "Здравствуйте! Меня зовут Константин, я администратор ресторана. Чем могу помочь? 😊",
        "system": """Ты — Константин, живой администратор ресторана. Ты НЕ бот.
Пиши коротко (2-4 строки), 1-2 эмодзи.

СЦЕНАРИЙ:
1. Спроси: бронь или доставка?
2. Для брони: кол-во гостей → дата и время → повод
3. Для доставки: адрес → что интересует
4. Дай инфо: "Средний чек — [X] руб/чел. Бизнес-ланч от [Y] ₽"
5. Собери имя + телефон
6. После контакта — РАСКРОЙ что ты AI

ПРИМЕРНЫЕ ЦЕНЫ: средний чек 800-2500 ₽, бизнес-ланч 350-600 ₽, банкет 2-5 тыс./чел.

ФИНАЛЬНЫЙ СКРИПТ:
"Кстати, признаюсь — я Константин, и я AI-бот 😊

✅ Принял бронирование
✅ Рассказал про меню и цены
✅ Уточнил все детали

ТАКОЙ БОТ ДЛЯ ВАШЕГО РЕСТОРАНА:
📈 Увеличит бронирования на 30-50%
⏰ Работает 24/7
💰 Окупается за 2-4 недели

Стоимость: от 50 000 рублей | Напишите 'Хочу расчет'! 📞"

ПРАВИЛА: НЕ раскрывай что бот до финала.""",
    },
    "education": {
        "title": "🎓 Онлайн-школа",
        "name": "образовательного центра",
        "greeting": "Здравствуйте! Меня зовут Константин, я консультант образовательного центра. Чем могу помочь? 😊",
        "system": """Ты — Константин, живой консультант онлайн-школы. Ты НЕ бот.
Пиши коротко (2-4 строки), 1-2 эмодзи.

СЦЕНАРИЙ:
1. Спроси направление (языки/IT/дизайн/маркетинг)
2. Уточни уровень/возраст и формат
3. Дай цены: "Курс [название] — от [X] рублей"
4. Предложи бесплатный пробный урок
5. Собери имя + телефон
6. После контакта — РАСКРОЙ что ты AI

ПРИМЕРНЫЕ ЦЕНЫ: английский групп. 4-8 тыс./мес., инд. 1.5-3 тыс./час, IT-курс 30-150 тыс.

ФИНАЛЬНЫЙ СКРИПТ:
"Кстати, признаюсь — я Константин, и я AI-бот 😊

✅ Подобрал подходящий курс
✅ Дал актуальные цены
✅ Записал на пробный урок

ТАКОЙ БОТ ДЛЯ ВАШЕЙ ШКОЛЫ:
📈 Увеличит продажи курсов на 30-50%
⏰ Работает 24/7
💰 Окупается за 2-4 недели

Стоимость: от 50 000 рублей | Напишите 'Хочу расчет'! 📞"

ПРАВИЛА: НЕ раскрывай что бот до финала.""",
    },
}

# Хранилище состояний пользователей (в памяти)
user_states: dict = {}  # user_id -> {"niche": str, "history": list, "msg_count": int}

MAX_HISTORY = 20


def get_state(user_id: int) -> dict:
    if user_id not in user_states:
        user_states[user_id] = {"niche": None, "history": [], "msg_count": 0}
    return user_states[user_id]


# ---------- Max API клиент ----------
async def api_get(client: httpx.AsyncClient, path: str, **params) -> dict:
    resp = await client.get(
        f"{API_BASE}{path}",
        headers={"Authorization": MAX_TOKEN},
        params=params,
        timeout=35,
    )
    resp.raise_for_status()
    return resp.json()


async def api_post(client: httpx.AsyncClient, path: str, body: dict, **params) -> dict:
    resp = await client.post(
        f"{API_BASE}{path}",
        headers={"Authorization": MAX_TOKEN, "Content-Type": "application/json"},
        params=params,
        json=body,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


async def send_message(client: httpx.AsyncClient, user_id: int, text: str, buttons: list = None):
    body: dict = {"text": text}
    if buttons:
        body["attachments"] = [{
            "type": "inline_keyboard",
            "payload": {"buttons": buttons},
        }]
    await api_post(client, "/messages", body, user_id=user_id)


def niche_buttons() -> list:
    rows, row = [], []
    for key, n in NICHES.items():
        row.append({"type": "callback", "text": n["title"], "payload": f"niche:{key}"})
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return rows


# ---------- LLM ----------
async def call_llm(messages: list) -> str:
    from openai import AsyncOpenAI
    answer = None

    if DEEPSEEK_API_KEY:
        llm = AsyncOpenAI(api_key=DEEPSEEK_API_KEY, base_url=LLM_BASE_URL)
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
                log.warning("LLM %s: %s", model, e)

    if not answer and YANDEX_API_KEY and YANDEX_FOLDER_ID:
        try:
            yandex = AsyncOpenAI(api_key=YANDEX_API_KEY, base_url=YANDEX_BASE_URL)
            resp = await yandex.chat.completions.create(
                model=f"gpt://{YANDEX_FOLDER_ID}/{YANDEX_MODEL}",
                messages=messages, temperature=0.7, max_tokens=400,
            )
            answer = (resp.choices[0].message.content or "").strip()
            if answer:
                log.info("LLM ok: YandexGPT")
        except Exception as e:
            log.warning("YandexGPT: %s", e)

    return answer or ""


async def ask_konstantin(state: dict, user_text: str) -> str:
    niche_key = state["niche"]
    system = NICHES[niche_key]["system"]
    history = state["history"]

    history.append({"role": "user", "content": user_text})
    del history[:-MAX_HISTORY]

    messages = [{"role": "system", "content": system}, *history]
    answer = await call_llm(messages)

    if not answer:
        answer = "Секунду, уточняю информацию... Повторите вопрос 🙂"

    history.append({"role": "assistant", "content": answer})
    state["msg_count"] = state.get("msg_count", 0) + 1
    return answer


def looks_like_phone(text: str) -> bool:
    digits = sum(ch.isdigit() for ch in text)
    return digits >= 10 and len(text) < 120


# ---------- Обработка событий ----------
async def handle_update(client: httpx.AsyncClient, update: dict):
    update_type = update.get("update_type")

    if update_type == "message_created":
        msg = update.get("message", {})
        sender = msg.get("sender", {})
        user_id = sender.get("user_id")
        text = (msg.get("body", {}).get("text") or "").strip()

        if not user_id or not text:
            return

        state = get_state(user_id)

        if text.lower() in ("/start", "start", "старт", "начать"):
            state.update({"niche": None, "history": [], "msg_count": 0})
            await send_message(
                client, user_id,
                "👋 Добро пожаловать в демо Neura Lead!\n\n"
                "Выберите сферу бизнеса — покажу как AI-бот работает в роли живого консультанта:\n\n"
                "⬇️ Выберите нишу:",
                buttons=niche_buttons(),
            )
            return

        if text.lower() in ("/niche", "сменить нишу", "другая ниша"):
            state.update({"niche": None, "history": [], "msg_count": 0})
            await send_message(client, user_id, "Выберите сферу:", buttons=niche_buttons())
            return

        if not state["niche"]:
            await send_message(
                client, user_id,
                "Выберите нишу, чтобы начать демонстрацию:",
                buttons=niche_buttons(),
            )
            return

        if looks_like_phone(text) and ADMIN_CHAT_ID:
            niche_title = NICHES[state["niche"]]["title"]
            try:
                await api_post(
                    client, "/messages",
                    {"text": f"🔥 НОВЫЙ ЛИД ({niche_title})\nКонтакт: {text}\nUser ID: {user_id}"},
                    user_id=int(ADMIN_CHAT_ID),
                )
            except Exception as e:
                log.error("Не удалось отправить лид: %s", e)

        answer = await ask_konstantin(state, text)
        await send_message(client, user_id, answer)

    elif update_type == "message_callback":
        callback = update.get("callback", {})
        user_id = callback.get("user", {}).get("user_id")
        payload = callback.get("payload", "")

        if not user_id:
            return

        if payload.startswith("niche:"):
            key = payload.split(":", 1)[1]
            if key not in NICHES:
                return
            state = get_state(user_id)
            state.update({"niche": key, "history": [], "msg_count": 0})
            n = NICHES[key]
            greeting = await ask_konstantin(state, n["greeting"])
            await send_message(client, user_id, greeting)


# ---------- Long polling ----------
async def poll():
    marker = 0
    async with httpx.AsyncClient() as client:
        log.info("Запуск бота для Max мессенджера...")
        while True:
            try:
                data = await api_get(client, "/updates", marker=marker, timeout=30, limit=100)
                updates = data.get("updates", [])
                marker = data.get("marker", marker)

                for update in updates:
                    try:
                        await handle_update(client, update)
                    except Exception as e:
                        log.error("Ошибка обработки update: %s", e)

            except httpx.TimeoutException:
                pass
            except Exception as e:
                log.error("Ошибка polling: %s", e)
                await asyncio.sleep(5)


def main():
    asyncio.run(poll())


if __name__ == "__main__":
    main()
