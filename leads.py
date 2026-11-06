"""Поиск телефона в тексте и оформление карточки заявки."""

from __future__ import annotations

import re

_PHONE_RE = re.compile(r"(?:\+?7|8)[\s\-()]*\d{3}[\s\-()]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}")


def extract_phone(text: str) -> str | None:
    """Российский номер → +7XXXXXXXXXX, иначе None."""
    m = _PHONE_RE.search(text or "")
    if not m:
        return None
    digits = re.sub(r"\D", "", m.group(0))
    if len(digits) != 11:
        return None
    return "+7" + digits[1:]


SAVE_LEAD_TOOL = {
    "type": "function",
    "function": {
        "name": "save_lead",
        "description": "Сохранить заявку и сразу уведомить менеджера. Вызывай, когда клиент оставил телефон или явно готов заказать.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Имя клиента"},
                "phone": {"type": "string", "description": "Телефон"},
                "company": {"type": "string", "description": "Компания или вид бизнеса"},
                "interest": {"type": "string", "enum": ["реклама в лифтах", "ИИ-бот", "реклама + бот", "УК/ТСЖ", "другое"]},
                "summary": {"type": "string", "description": "Коротко: что хочет клиент, формат, зоны, срок, расчёт"},
            },
            "required": ["interest", "summary"],
        },
    },
}


def lead_card(lead: dict, who: str = "") -> str:
    lines = ["🔥 Новая заявка"]
    if who:
        lines.append(who)
    for label, key in (("Имя", "name"), ("Телефон", "phone"), ("Компания", "company"),
                       ("Интерес", "interest"), ("Суть", "summary")):
        if lead.get(key):
            lines.append(f"{label}: {lead[key]}")
    return "\n".join(lines)
