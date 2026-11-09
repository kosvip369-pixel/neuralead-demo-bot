"""
База знаний «Наш дом. Медиа» × NeuraLead — единый источник цен и правил для обоих ботов.

Меняете цену или правило — меняйте ТОЛЬКО здесь. Файл одинаковый в репозиториях
neuralead-bot и neuralead-demo-bot (скопируйте его в оба после правки).
Прайс действует с ноября 2026 (решение от 04.11.2026).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date

# ---------------------------------------------------------------- контакты
# Можно переопределить переменными окружения на хостинге.
NASHDOM_CONTACT_NAME = os.getenv("NASHDOM_CONTACT_NAME", "Илья Досмедов")
NASHDOM_PHONE = os.getenv("NASHDOM_PHONE", "8 (995) 500-71-80")
NASHDOM_SITE = os.getenv("NASHDOM_SITE", "https://kosvip369-pixel.github.io/nashdom-media/")
NEURALEAD_CONTACT_NAME = os.getenv("NEURALEAD_CONTACT_NAME", "Константин")
NEURALEAD_PHONE = os.getenv("NEURALEAD_PHONE", "+7 920 698-08-58")
NEURALEAD_TG = os.getenv("NEURALEAD_TG", "t.me/Kos2323")
NEURALEAD_CHANNEL = os.getenv("NEURALEAD_CHANNEL", "t.me/neuralead_ru")
NEURALEAD_SITE = os.getenv("NEURALEAD_SITE", "https://neuralead-demo.netlify.app")

# ---------------------------------------------------------------- стенды
# Ставка за 1 лифтборд в месяц, ₽. Макет и печать включены.
FORMATS: dict[str, dict] = {
    "A1": {"rate": 1100, "what": "весь стенд (8 ячеек А4)"},
    "A2": {"rate": 640, "what": "половина стенда (4 ячейки)"},
    "A3": {"rate": 360, "what": "2 ячейки А4"},
    "A4": {"rate": 200, "what": "1 ячейка А4"},
    "A5": {"rate": 115, "what": "½ ячейки, минимальный формат для QR-кода"},
    "A6": {"rate": 65, "what": "¼ ячейки"},
    "A7": {"rate": 40, "what": "визитка, ⅛ ячейки"},
}

ZONES: dict[str, dict] = {
    "Попова": {"code": "З1", "lifts": 51, "houses": 14, "streets": "Попова, Новая, Весенняя, К. Маркса"},
    "Космонавтов": {"code": "З2", "lifts": 53, "houses": 18, "streets": "Космонавтов, Автодорожная, Александрова"},
    "Курчатова": {"code": "З3", "lifts": 54, "houses": 17, "streets": "пр-кт Курчатова, Энергетиков, Левитана"},
    "Энтузиастов": {"code": "З4", "lifts": 49, "houses": 18, "streets": "Энтузиастов, Энергетиков, Венецианова"},
}
TOTAL_LIFTS = sum(z["lifts"] for z in ZONES.values())  # 207

GEO_DISCOUNT = {1: 0.0, 2: 0.05, 3: 0.05, 4: 0.10}          # половина города −5 %, весь город −10 %
TERM_DISCOUNT = {1: 0.0, 3: 0.05, 6: 0.10, 12: 0.15}         # срок 3 / 6 / 12 мес
FOUNDERS_DISCOUNT = 0.30            # первые 15 договоров, фиксация на 6 мес, НЕ суммируется с другими скидками
FOUNDERS_SLOTS = 15
EXCLUSIVE_SURCHARGE = 0.40          # эксклюзив категории на стенде
ADDRESSES_SURCHARGE = 0.30          # выборочные адреса вместо зоны, минимум 20 стендов
MASTERS_PRICE = 990                 # «Справочник мастеров»: визитка A7 в блоке мастеров, ₽/мес за зону, оплата за 3 мес

# ---------------------------------------------------------------- ИИ-боты NeuraLead
BOT_TARIFFS = {
    "Подписка": {"setup": 15000, "monthly": 9900, "min_months": 6,
                 "note": "основной тариф"},
    "Покупка": {"setup": 50000, "monthly": 4900, "min_months": 1,
                "note": "бот выкупается, 4 900 ₽/мес — сопровождение"},
}

KNOWLEDGE_TEXT = f"""
=== ГЕОГРАФИЯ — ВАЖНО ===
• Реклама на стендах в лифтах («Наш дом. Медиа») — только город Удомля (Тверская обл.).
• ИИ-боты NeuraLead — для бизнеса из ЛЮБОГО города и региона России (Москва, Петербург, Иркутск — без разницы):
  всё делаем дистанционно — обсуждение, настройка, запуск и поддержка онлайн, приезжать никуда не нужно.
• Связка «Реклама + заявки» (QR на стенде → ИИ-бот) — для бизнеса, работающего в Удомле.
Никогда не говори, что «работаем только в Удомле» про ботов. Если клиент из другого города — сразу переходи к ИИ-боту.

=== «НАШ ДОМ. МЕДИА» — РЕКЛАМА НА СТЕНДАХ В ЛИФТАХ УДОМЛИ ===
Что это: информационные стенды А1 (841×594 мм) в кабинах {TOTAL_LIFTS} лифтов 67 многоэтажных домов Удомли
(6–16 этажей). Около 15 500 жителей (≈63 % города) видят стенды каждый день, 2–4 поездки в день, 20–40 секунд внимания.
Стенд разделён на 8 ячеек А4. Одна ячейка — «ячейка дома»: бесплатно для управляющей компании (контакты УК,
диспетчерская, аварийные службы). Стенды под антивандальной рамкой с прозрачной панелью.

Форматы и ставка за 1 стенд в месяц (макет и печать включены):
A1 1 100 ₽ (весь стенд) · A2 640 ₽ (½ стенда) · A3 360 ₽ (2 ячейки) · A4 200 ₽ (1 ячейка) ·
A5 115 ₽ (½ ячейки) · A6 65 ₽ (¼ ячейки) · A7 40 ₽ (визитка).

Зоны (новая Удомля, южнее ж/д): Попова — 51 лифт; Космонавтов — 53; Курчатова — 54; Энтузиастов — 49. Весь город — {TOTAL_LIFTS}.
Цена за месяц = ставка × число лифтов в выбранных зонах, со скидками. Округление до 10 ₽.
Примеры за месяц без скидки за срок: A4 одна зона 9 800–10 800 ₽; A4 весь город ≈ 37 260 ₽; A5 одна зона 5 640–6 210 ₽.

Скидки: 2–3 зоны −5 %, весь город −10 %; срок 3 / 6 / 12 мес — −5 / −10 / −15 % (скидки перемножаются).
Цена первых клиентов: первые {FOUNDERS_SLOTS} договоров — −30 % от прайса с фиксацией на 6 месяцев; не суммируется с другими скидками.
Надбавки: эксклюзив категории на стенде +40 %; выборочные адреса вместо зоны +30 % (минимум 20 стендов).
«Справочник мастеров» для частных мастеров: визитка в блоке мастеров — {MASTERS_PRICE} ₽/мес за зону при оплате за 3 месяца.
Не размещаем: микрозаймы, ставки/казино, политическую агитацию, 18+.

Как работаем: выпуски 1-го и 15-го числа. Приём материалов: до 25-го на выпуск 1-го, до 10-го на выпуск 15-го.
Минимальный заказ — 1 зона на 1 месяц, предоплата 100 % за первый период. Макет делаем бесплатно за 2 рабочих дня,
печать за наш счёт. Фотоотчёт по адресам — в течение 2 дней после выхода, плюс акт и чек.
QR-код ставим на модули от A5; у каждой зоны свой код, промокод «ЛИФТ» отмечает заказы со стендов.

Управляющим компаниям и ТСЖ: стенд ставим и обслуживаем бесплатно, ячейка дома — бесплатно, антивандальная рамка,
обход 2 раза в месяц, фотоотчёт в УК, документы готовим сами, начинаем с пилота на одном доме. Деньги с УК не берём.

=== NEURALEAD — ИИ-БОТЫ ДЛЯ БИЗНЕСА (MAX и Telegram) ===
Бот отвечает клиентам 24/7, знает услуги, цены и график, принимает заказы и записи, сложное передаёт администратору,
сохраняет базу клиентов и умеет напоминать о бизнесе (сезон, акции). Кнопочных ботов не делаем — только ИИ-боты.
Тарифы:
• «Подписка» — запуск 15 000 ₽ + 9 900 ₽/мес, договор от 6 месяцев. Основной тариф.
• «Покупка» — 50 000 ₽ разово + 4 900 ₽/мес сопровождение.
В оба входит: до 1 000 диалогов в месяц, правки меню/цен/акций по просьбе, ежемесячный отчёт по заявкам и QR-кодам.
Запуск 7–10 дней. Если клиент прекращает подписку — база клиентов и переписка выгружаются ему, бот отключается;
забрать бота себе можно по тарифу «Покупка».

=== СВЯЗКА «РЕКЛАМА + ЗАЯВКИ» ===
• Реклама на стендах от 6 месяцев → ИИ-бот «Подписка» без платы за запуск (0 ₽ вместо 15 000), далее 9 900 ₽/мес.
• Клиенту с ИИ-ботом NeuraLead → первый месяц модуля A5 в его зоне в подарок.
Как работает: житель видит модуль с QR в лифте → наводит камеру → попадает в ИИ-бота бизнеса в MAX/Telegram →
бот принимает заказ или запись → раз в месяц отчёт: сколько заявок пришло из каждой зоны.

=== КОНТАКТЫ ===
«Наш дом. Медиа»: {NASHDOM_CONTACT_NAME}, {NASHDOM_PHONE}, сайт {NASHDOM_SITE}
NeuraLead: {NEURALEAD_CONTACT_NAME}, {NEURALEAD_PHONE}, Telegram {NEURALEAD_TG}, канал {NEURALEAD_CHANNEL}, сайт {NEURALEAD_SITE}
""".strip()


# ---------------------------------------------------------------- калькулятор
@dataclass
class Quote:
    fmt: str
    zones: list[str]
    months: int
    lifts: int
    base_month: int                 # без скидок и надбавок
    month: int                      # итог в месяц
    total: int                      # за весь срок
    discounts: list[str] = field(default_factory=list)
    surcharges: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_text(self) -> str:
        zones = "весь город" if len(self.zones) == len(ZONES) else ", ".join(self.zones)
        lines = [
            f"Модуль {self.fmt} · {zones} ({self.lifts} лифтов) · {self.months} мес.",
            f"Прайс: {FORMATS[self.fmt]['rate']} ₽ × {self.lifts} = {fmt_rub(self.base_month)} в месяц",
        ]
        if self.surcharges:
            lines.append("Надбавки: " + "; ".join(self.surcharges))
        if self.discounts:
            lines.append("Скидки: " + "; ".join(self.discounts))
        lines.append(f"Итого: {fmt_rub(self.month)} в месяц, {fmt_rub(self.total)} за {self.months} мес.")
        lines += self.notes
        return "\n".join(lines)

    def as_dict(self) -> dict:
        return {"format": self.fmt, "zones": self.zones, "months": self.months, "lifts": self.lifts,
                "base_month_rub": self.base_month, "month_rub": self.month, "total_rub": self.total,
                "discounts": self.discounts, "surcharges": self.surcharges, "notes": self.notes,
                "text": self.as_text()}


def fmt_rub(n: int | float) -> str:
    return f"{int(round(n)):,}".replace(",", " ") + " ₽"


def _round10(x: float) -> int:
    return int(round(x / 10.0)) * 10


def normalize_zones(zones) -> list[str]:
    """Принимает список названий/кодов зон, «весь город», «all» и т. п."""
    if zones is None:
        return []
    if isinstance(zones, str):
        zones = [zones]
    out: list[str] = []
    for z in zones:
        s = str(z).strip().lower()
        if s in ("all", "весь город", "город", "все", "все зоны", "вся удомля"):
            return list(ZONES)
        for name, info in ZONES.items():
            if s in (name.lower(), info["code"].lower()) or name.lower().startswith(s[:5]) and len(s) >= 4:
                if name not in out:
                    out.append(name)
    return out


def calc_ad_price(fmt: str, zones, months: int = 1, founders: bool = False,
                  exclusive: bool = False) -> Quote:
    fmt = str(fmt).upper().replace("А", "A").strip()   # кириллическая «А» → латинская
    if fmt not in FORMATS:
        raise ValueError(f"Нет формата {fmt}. Есть: {', '.join(FORMATS)}")
    zl = normalize_zones(zones)
    if not zl:
        raise ValueError("Не указаны зоны. Есть: " + ", ".join(ZONES) + " или «весь город»")
    months = int(months)
    if months < 1:
        raise ValueError("Срок — от 1 месяца")
    lifts = sum(ZONES[z]["lifts"] for z in zl)
    rate = FORMATS[fmt]["rate"]
    base = rate * lifts
    price = float(base)
    q = Quote(fmt=fmt, zones=zl, months=months, lifts=lifts, base_month=base, month=0, total=0)

    if exclusive:
        price *= 1 + EXCLUSIVE_SURCHARGE
        q.surcharges.append("эксклюзив категории +40 %")

    if founders:
        price *= 1 - FOUNDERS_DISCOUNT
        q.discounts.append("цена первых клиентов −30 % (фиксация на 6 мес., другие скидки не суммируются)")
    else:
        geo = GEO_DISCOUNT[len(zl)]
        if geo:
            price *= 1 - geo
            q.discounts.append(("весь город" if len(zl) == 4 else f"{len(zl)} зоны") + f" −{int(geo * 100)} %")
        term_key = max(k for k in TERM_DISCOUNT if k <= months)
        term = TERM_DISCOUNT[term_key]
        if term:
            price *= 1 - term
            q.discounts.append(f"срок от {term_key} мес. −{int(term * 100)} %")

    q.month = _round10(price)
    q.total = q.month * months
    if months >= 6:
        q.notes.append("Бонус: при рекламе от 6 месяцев ИИ-бот «Подписка» запускается бесплатно (0 ₽ вместо 15 000).")
    if fmt in ("A6", "A7"):
        q.notes.append("QR-код ставим на модули от A5.")
    return q


def next_issue(today: date | None = None) -> dict:
    """Ближайший выпуск (1-е или 15-е) и крайний срок приёма материалов."""
    d = today or date.today()
    y, m = d.year, d.month

    def add_month(yy, mm):
        return (yy + 1, 1) if mm == 12 else (yy, mm + 1)

    if d.day <= 10:
        issue, deadline = date(y, m, 15), date(y, m, 10)
    elif d.day <= 25:
        ny, nm = add_month(y, m)
        issue, deadline = date(ny, nm, 1), date(y, m, 25)
    else:
        ny, nm = add_month(y, m)
        issue, deadline = date(ny, nm, 15), date(ny, nm, 10)
    return {"issue": issue.isoformat(), "deadline": deadline.isoformat()}


# ---------------------------------------------------------------- схема инструмента для ИИ
CALC_TOOL = {
    "type": "function",
    "function": {
        "name": "calc_ad_price",
        "description": "Точно рассчитать стоимость рекламы на стендах в лифтах Удомли. Вызывай ВСЕГДА, когда называешь цену размещения.",
        "parameters": {
            "type": "object",
            "properties": {
                "format": {"type": "string", "enum": list(FORMATS), "description": "Формат модуля"},
                "zones": {"type": "array", "items": {"type": "string"},
                          "description": "Зоны: Попова, Космонавтов, Курчатова, Энтузиастов или ['весь город']"},
                "months": {"type": "integer", "description": "Срок в месяцах (1, 3, 6, 12 и т. д.)"},
                "founders": {"type": "boolean", "description": "Применить цену первых клиентов (−30 %)"},
                "exclusive": {"type": "boolean", "description": "Эксклюзив категории (+40 %)"},
            },
            "required": ["format", "zones"],
        },
    },
}


def run_calc_tool(args: dict) -> dict:
    try:
        q = calc_ad_price(args.get("format", ""), args.get("zones"), args.get("months", 1) or 1,
                          bool(args.get("founders")), bool(args.get("exclusive")))
        return q.as_dict()
    except Exception as e:  # ИИ передал неверные данные — вернём понятную ошибку
        return {"error": str(e)}
