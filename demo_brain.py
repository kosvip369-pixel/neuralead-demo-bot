"""
Мозг демо-бота «Наш дом. Медиа × NeuraLead» (общий для Telegram и MAX).

Два режима:
  • assistant — открытый ИИ-ассистент двух компаний: объясняет, считает цену, берёт заявку;
  • demo      — «Показать на моём бизнесе»: бот играет роль ИИ-бота бизнеса клиента.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Awaitable, Callable

import knowledge as kb
from leads import SAVE_LEAD_TOOL, extract_phone, lead_card
from llm import default_completion, run_agent
from storage import Storage

log = logging.getLogger("demo-brain")

HISTORY_LIMIT = 20
FALLBACK = ("Не получилось ответить — сервис ИИ сейчас недоступен. Напишите ещё раз через минуту "
            f"или позвоните: {kb.NASHDOM_PHONE}.")

# ------------------------------------------------------------------ тексты
WELCOME = (
    "Здравствуйте! Я ИИ-бот «Наш дом. Медиа» × NeuraLead 🤖\n\n"
    "Отвечаю круглосуточно и понимаю обычный текст. Могу:\n"
    "• рассказать про рекламу на стендах в 207 лифтах Удомли и сразу посчитать цену;\n"
    "• объяснить, как работает QR-код на модуле и ИИ-бот, который принимает заказы;\n"
    "• показать на вашем бизнесе, как будет отвечать ваш собственный бот.\n\n"
    "Напишите вопрос своими словами или выберите кнопку."
)

MENU = [
    [("📍 Реклама в лифтах", "menu:lifts"), ("🤖 ИИ-бот для бизнеса", "menu:bot")],
    [("🎭 Показать на моём бизнесе", "menu:demo"), ("🧮 Рассчитать цену", "menu:calc")],
    [("📞 Связаться с менеджером", "menu:contact")],
]
DEMO_MENU = [[("⬅️ Выйти из демо", "demo:exit")]]

MENU_PROMPTS = {
    "menu:lifts": "Расскажите коротко про рекламу в лифтах: где стенды, какие форматы и сколько стоит.",
    "menu:bot": "Расскажите про ИИ-бота для бизнеса: что он умеет и сколько стоит.",
    "menu:calc": "Хочу рассчитать стоимость рекламы в лифтах. Помогите подобрать формат и зоны.",
}

CONTACTS = (
    "Связаться с живым менеджером:\n"
    f"• Реклама в лифтах («Наш дом. Медиа») — {kb.NASHDOM_CONTACT_NAME}, {kb.NASHDOM_PHONE}\n"
    f"• ИИ-боты (NeuraLead) — {kb.NEURALEAD_CONTACT_NAME}, {kb.NEURALEAD_PHONE}, {kb.NEURALEAD_TG}\n\n"
    "Или оставьте здесь имя и телефон — менеджер перезвонит сам."
)

ASK_BUSINESS = ("Отлично! Напишите, какой у вас бизнес — например «пиццерия на Курчатова» или "
                "«автосервис, шиномонтаж». Я покажу, как ваш ИИ-бот будет отвечать вашим клиентам.")


def assistant_system(today: date | None = None) -> str:
    ni = kb.next_issue(today)
    return f"""Ты — ИИ-бот компаний «Наш дом. Медиа» (реклама на стендах в лифтах Удомли) и NeuraLead (ИИ-боты для бизнеса).
Ты одновременно консультант и живой пример того, как ИИ-бот общается с клиентами. Ты открыто бот — не притворяйся человеком.

Как общаться:
- Пиши по-русски, коротко и по делу: 2–5 предложений, без длинных списков. Тон — дружелюбный, деловой, без канцелярита.
- Задавай по одному вопросу за раз и веди к заявке: формат → зоны → срок → расчёт → имя и телефон.
- Цену размещения называй ТОЛЬКО после вызова инструмента calc_ad_price. Не придумывай скидок, которых нет в базе знаний.
- Если спрашивают про QR-код — объясни связку: модуль с QR в лифте → житель сканирует → попадает в ИИ-бота бизнеса → бот принимает заказ → отчёт по зонам.
- Если человек хочет увидеть бота на своём бизнесе — вызови start_demo с описанием бизнеса.
- Когда клиент оставил телефон или готов заказать — вызови save_lead и скажи, что менеджер свяжется сегодня.
- Если вопрос вне темы (договор, нестандартные условия, юридическое) — предложи связаться с менеджером и дай контакт.
- Сегодня {(today or date.today()).isoformat()}. Ближайший выпуск стендов {ni['issue']}, материалы принимаем до {ni['deadline']}.

БАЗА ЗНАНИЙ:
{kb.KNOWLEDGE_TEXT}"""


def demo_system(business: str) -> str:
    return f"""Сейчас ДЕМО-РЕЖИМ. Ты — ИИ-бот бизнеса: «{business}» (Удомля). Тебе пишет человек и играет роль клиента этого бизнеса.
Отвечай так, как отвечал бы хороший бот этого бизнеса: приветливо, коротко (2–4 предложения), с конкретикой.
Придумай правдоподобные услуги, цены и свободное время для примера — это демонстрация. Принимай заказ или запись,
уточняй детали, повторяй итог заказа. Если клиент пришёл по QR из лифта — предложи промокод «ЛИФТ» (небольшой подарок).
Не говори про рекламу в лифтах и тарифы NeuraLead, пока клиент сам не спросит или не выйдет из демо.
Если спросят «ты бот?» — честно скажи, что ты ИИ-бот (это демо NeuraLead)."""


DEMO_TOOL = {
    "type": "function",
    "function": {
        "name": "start_demo",
        "description": "Включить демо-режим: бот разыграет, как ИИ-бот отвечал бы клиентам бизнеса пользователя.",
        "parameters": {"type": "object",
                       "properties": {"business": {"type": "string", "description": "Бизнес пользователя, например «пиццерия»"}},
                       "required": ["business"]},
    },
}


class DemoBrain:
    """reply = await brain.handle(chat, channel, text) → {'text': str, 'buttons': [[(title, payload)]] | None}"""

    def __init__(self, storage: Storage, notify: Callable[[str], Awaitable[None]] | None = None,
                 completion=default_completion):
        self.db = storage
        self.notify = notify
        self.completion = completion

    # ---------------------------------------------------------- вход
    async def handle(self, chat: str, channel: str, text: str, who: str = "") -> dict:
        text = (text or "").strip()
        low = text.lower()
        if low in ("/start", "start", "старт", "начать", "меню", "/menu"):
            self.db.clear_history(chat)
            self.db.set_state(chat, mode="assistant", business=None, awaiting_business=None)
            return {"text": WELCOME, "buttons": MENU}
        if low in ("/exit", "выход", "выйти", "стоп демо") or text == "demo:exit":
            return await self._exit_demo(chat)
        if text == "menu:contact":
            return {"text": CONTACTS, "buttons": MENU}
        if text == "menu:demo":
            self.db.set_state(chat, awaiting_business=True)
            return {"text": ASK_BUSINESS, "buttons": None}
        if text in MENU_PROMPTS:
            text = MENU_PROMPTS[text]

        state = self.db.get_state(chat)
        if state.get("awaiting_business"):
            self.db.set_state(chat, awaiting_business=None)
            return await self._start_demo(chat, text)
        if state.get("mode") == "demo" and state.get("business"):
            return await self._demo_turn(chat, state["business"], text)
        return await self._assistant_turn(chat, channel, text, who)

    # ---------------------------------------------------------- режим ассистента
    async def _assistant_turn(self, chat: str, channel: str, text: str, who: str) -> dict:
        self.db.add_message(chat, "user", text)
        history = self.db.history(chat, HISTORY_LIMIT)
        saved_phones: list[str] = []
        demo_business: dict = {}

        async def save_lead(args: dict) -> dict:
            phone = extract_phone(args.get("phone", "")) or args.get("phone", "")
            if phone and self.db.lead_exists(chat, phone):
                return {"ok": True, "note": "заявка уже сохранена"}
            lead_id = self.db.add_lead(chat, channel, args.get("name", ""), phone, args.get("company", ""),
                                       args.get("interest", ""), args.get("summary", ""))
            saved_phones.append(phone)
            await self._notify(lead_card(args | {"phone": phone}, who))
            return {"ok": True, "lead_id": lead_id}

        def start_demo(args: dict) -> dict:
            demo_business["name"] = args.get("business", "").strip()
            return {"ok": True}

        try:
            reply, done = await run_agent(
                assistant_system(), history,
                tools=[kb.CALC_TOOL, SAVE_LEAD_TOOL, DEMO_TOOL],
                handlers={"calc_ad_price": kb.run_calc_tool, "save_lead": save_lead, "start_demo": start_demo},
                completion=self.completion,
            )
        except Exception as e:
            log.error("ИИ не ответил: %s", e)
            reply, done = "", []

        # страховка: телефон в сообщении, а ИИ заявку не сохранил
        phone = extract_phone(text)
        if phone and phone not in saved_phones and not self.db.lead_exists(chat, phone):
            self.db.add_lead(chat, channel, phone=phone, summary="Телефон из сообщения: " + text[:300])
            await self._notify(lead_card({"phone": phone, "summary": text[:300]}, who))

        if demo_business.get("name"):
            return await self._start_demo(chat, demo_business["name"], lead_in=reply)

        reply = reply or FALLBACK
        self.db.add_message(chat, "assistant", reply)
        return {"text": reply, "buttons": None}

    # ---------------------------------------------------------- демо-режим
    async def _start_demo(self, chat: str, business: str, lead_in: str = "") -> dict:
        business = business.strip()[:120] or "ваш бизнес"
        self.db.set_state(chat, mode="demo", business=business)
        intro = (f"🎭 Демо: так ваш ИИ-бот будет отвечать клиентам «{business}».\n"
                 "Пишите как ваш клиент — например «хочу заказать», «сколько стоит», «есть время в субботу?».\n"
                 "Выйти из демо — кнопка ниже или слово «выход».")
        first = ""
        try:
            first, _ = await run_agent(demo_system(business),
                                       [{"role": "user", "content": "(клиент открыл чат, поприветствуй его)"}],
                                       completion=self.completion)
        except Exception as e:
            log.error("Демо не стартовало: %s", e)
        dkey = chat + ":demo"
        self.db.clear_history(dkey)
        if first:
            self.db.add_message(dkey, "assistant", first)
        text = intro + ("\n\n" + first if first else "")
        if lead_in and lead_in not in text:
            text = lead_in + "\n\n" + text
        return {"text": text, "buttons": DEMO_MENU}

    async def _demo_turn(self, chat: str, business: str, text: str) -> dict:
        dkey = chat + ":demo"
        self.db.add_message(dkey, "user", text)
        try:
            reply, _ = await run_agent(demo_system(business), self.db.history(dkey, HISTORY_LIMIT),
                                       completion=self.completion)
        except Exception as e:
            log.error("ИИ не ответил в демо: %s", e)
            reply = ""
        reply = reply or FALLBACK
        self.db.add_message(dkey, "assistant", reply)
        return {"text": reply, "buttons": DEMO_MENU}

    async def _exit_demo(self, chat: str) -> dict:
        state = self.db.get_state(chat)
        business = state.get("business") or "вашего бизнеса"
        self.db.set_state(chat, mode="assistant", business=None, awaiting_business=None)
        self.db.clear_history(chat + ":demo")
        text = (f"Вот так бот отвечал бы клиентам «{business}» — днём и ночью, без выходных.\n\n"
                "Такой бот для вашего бизнеса:\n"
                "• «Подписка» — запуск 15 000 ₽ + 9 900 ₽/мес (договор от 6 мес.);\n"
                "• «Покупка» — 50 000 ₽ + 4 900 ₽/мес сопровождение.\n"
                "При рекламе в лифтах от 6 месяцев запуск бота бесплатно, а QR на модуле приводит к нему клиентов.\n\n"
                "Оставьте имя и телефон — менеджер посчитает под ваш бизнес.")
        self.db.add_message(chat, "assistant", text)
        return {"text": text, "buttons": MENU}

    async def _notify(self, text: str) -> None:
        if self.notify:
            try:
                await self.notify(text)
            except Exception as e:
                log.error("Не удалось уведомить менеджера: %s", e)
