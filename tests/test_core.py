"""Проверка логики без сети: python -m unittest discover -s tests -v"""

import asyncio
import json
import sys
import tempfile
import time
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import knowledge as kb  # noqa: E402
from leads import extract_phone  # noqa: E402
from storage import Storage  # noqa: E402


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


class FakeLLM:
    """Имитация модели: по очереди отдаёт заготовленные ответы и запоминает, что ей прислали."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    async def __call__(self, messages, tools):
        self.calls.append({"messages": messages, "tools": [t["function"]["name"] for t in (tools or [])]})
        step = self.script.pop(0) if self.script else {"content": "ок"}
        if "tool" in step:
            return {"content": "", "tool_calls": [{"id": f"c{len(self.calls)}", "name": step["tool"],
                                                    "arguments": json.dumps(step.get("args", {}), ensure_ascii=False)}]}
        return {"content": step["content"], "tool_calls": []}


class TestCalc(unittest.TestCase):
    def test_matches_site_and_price_doc(self):
        self.assertEqual(kb.calc_ad_price("A4", ["Энтузиастов"]).month, 9800)
        self.assertEqual(kb.calc_ad_price("A4", ["Курчатова"]).month, 10800)
        self.assertEqual(kb.calc_ad_price("A4", ["весь город"]).month, 37260)
        self.assertEqual(kb.calc_ad_price("A5", ["Энтузиастов"]).month, 5640)
        self.assertEqual(kb.calc_ad_price("A1", "all").month, 204930)

    def test_term_and_geo_multiply(self):
        q = kb.calc_ad_price("A4", ["Попова", "Космонавтов"], months=6)
        # 200 × 104 = 20 800; ×0,95 ×0,90 = 17 784 → 17 780
        self.assertEqual(q.month, 17780)
        self.assertEqual(q.total, 17780 * 6)
        self.assertTrue(any("бесплатно" in n for n in q.notes))

    def test_founders_not_combined(self):
        q = kb.calc_ad_price("A4", ["весь город"], months=12, founders=True)
        self.assertEqual(q.month, 28980)          # 41 400 × 0,7
        self.assertEqual(len(q.discounts), 1)

    def test_cyrillic_format_and_codes(self):
        self.assertEqual(kb.calc_ad_price("а3", ["з3"]).month, 360 * 54)

    def test_errors_go_back_to_ai(self):
        self.assertIn("error", kb.run_calc_tool({"format": "A9", "zones": ["Попова"]}))
        self.assertIn("error", kb.run_calc_tool({"format": "A4", "zones": ["Москва"]}))

    def test_next_issue(self):
        self.assertEqual(kb.next_issue(date(2026, 11, 6)), {"issue": "2026-11-15", "deadline": "2026-11-10"})
        self.assertEqual(kb.next_issue(date(2026, 11, 20)), {"issue": "2026-12-01", "deadline": "2026-11-25"})
        self.assertEqual(kb.next_issue(date(2026, 12, 28)), {"issue": "2027-01-15", "deadline": "2027-01-10"})


class TestLeadsAndStorage(unittest.TestCase):
    def test_phone(self):
        self.assertEqual(extract_phone("звоните 8 (920) 698-08-58"), "+79206980858")
        self.assertEqual(extract_phone("+7 995 500 71 80, Илья"), "+79955007180")
        self.assertIsNone(extract_phone("бюджет 1 500 000 рублей"))

    def test_storage_persists(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "t.db"
            s = Storage(p)
            s.add_message("c", "user", "привет")
            s.set_state("c", mode="demo", business="пицца")
            s.add_lead("c", "tg", phone="+7999")
            s2 = Storage(p)                      # «перезапуск»
            self.assertEqual(s2.history("c")[0]["content"], "привет")
            self.assertEqual(s2.get_state("c")["business"], "пицца")
            self.assertTrue(s2.lead_exists("c", "+7999"))


class TestDemoBrain(unittest.TestCase):
    def setUp(self):
        try:
            import demo_brain  # noqa: F401
        except ImportError:
            self.skipTest("демо-бот в этом репозитории не используется")
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Storage(Path(self.tmp.name) / "d.db")
        self.notes = []

        async def notify(t):
            self.notes.append(t)
        self.notify = notify

    def tearDown(self):
        self.tmp.cleanup()

    def brain(self, script):
        from demo_brain import DemoBrain
        self.llm = FakeLLM(script)
        return DemoBrain(self.db, notify=self.notify, completion=self.llm)

    def test_start_shows_menu_without_ai(self):
        b = self.brain([])
        out = run(b.handle("tg:1", "telegram", "/start"))
        self.assertIn("ИИ-бот", out["text"])
        self.assertTrue(out["buttons"])
        self.assertEqual(self.llm.calls, [])

    def test_price_question_uses_calculator(self):
        b = self.brain([
            {"tool": "calc_ad_price", "args": {"format": "A5", "zones": ["Курчатова"], "months": 6}},
            {"content": "Модуль A5 в зоне Курчатова на 6 мес — 5 590 ₽ в месяц."},
        ])
        out = run(b.handle("tg:1", "telegram", "Хочу рекламу в лифтах и QR-код, сколько на полгода в зоне Курчатова?"))
        self.assertIn("5 590", out["text"])
        tool_msg = [m for m in self.llm.calls[1]["messages"] if m["role"] == "tool"][0]
        self.assertEqual(json.loads(tool_msg["content"])["month_rub"], 5590)   # 115×54×0,9 = 5 589 → 5 590
        self.assertEqual(self.llm.calls[0]["tools"], ["calc_ad_price", "save_lead", "start_demo"])
        self.assertIn("не притворяйся человеком", self.llm.calls[0]["messages"][0]["content"])

    def test_lead_saved_and_owner_notified(self):
        b = self.brain([
            {"tool": "save_lead", "args": {"name": "Ольга", "phone": "8 920 111-22-33", "company": "Пиццерия",
                                           "interest": "реклама + бот", "summary": "A5 Курчатова 6 мес + бот"}},
            {"content": "Спасибо, Ольга! Менеджер позвонит сегодня."},
        ])
        run(b.handle("tg:2", "telegram", "Ольга, 8 920 111-22-33, пиццерия", who="Telegram: Ольга"))
        self.assertEqual(len(self.db.leads()), 1)                 # без дубля от страховки
        self.assertEqual(self.db.leads()[0]["phone"], "+79201112233")
        self.assertIn("Ольга", self.notes[0])

    def test_phone_safety_net_when_ai_forgets(self):
        b = self.brain([{"content": "Записал!"}])
        run(b.handle("max:3", "max", "мой номер +7 995 500 71 80"))
        self.assertEqual(self.db.leads()[0]["channel"], "max")
        self.assertEqual(len(self.notes), 1)

    def test_demo_button_flow(self):
        b = self.brain([
            {"content": "Здравствуйте! Пиццерия «Пример», что закажете?"},     # приветствие демо
            {"content": "Пепперони 30 см — 590 ₽. Доставить к 19:40?"},        # ход в демо
        ])
        out = run(b.handle("tg:4", "telegram", "menu:demo"))
        self.assertIn("какой у вас бизнес", out["text"])
        out = run(b.handle("tg:4", "telegram", "пиццерия"))
        self.assertIn("🎭 Демо", out["text"])
        self.assertIn("Здравствуйте", out["text"])
        out = run(b.handle("tg:4", "telegram", "хочу пепперони"))
        self.assertIn("590", out["text"])
        self.assertIn("ДЕМО-РЕЖИМ", self.llm.calls[-1]["messages"][0]["content"])
        self.assertEqual(self.db.leads(), [])                      # в демо заявки не создаются
        out = run(b.handle("tg:4", "telegram", "выход"))
        self.assertIn("9 900", out["text"])
        self.assertEqual(self.db.get_state("tg:4")["mode"], "assistant")

    def test_free_text_demo_request(self):
        b = self.brain([
            {"tool": "start_demo", "args": {"business": "автосервис"}},
            {"content": "Сейчас покажу!"},
            {"content": "Здравствуйте! Что с машиной?"},
        ])
        out = run(b.handle("tg:5", "telegram", "покажи как бот будет работать у моего автосервиса"))
        self.assertIn("автосервис", out["text"])
        self.assertEqual(self.db.get_state("tg:5")["mode"], "demo")

    def test_ai_down_gives_fallback(self):
        from demo_brain import DemoBrain

        async def broken(messages, tools):
            raise RuntimeError("нет сети")
        b = DemoBrain(self.db, completion=broken)
        out = run(b.handle("tg:6", "telegram", "привет"))
        self.assertIn(kb.NASHDOM_PHONE, out["text"])


class TestSales(unittest.TestCase):
    def setUp(self):
        try:
            import sales_brain  # noqa: F401
        except ImportError:
            self.skipTest("ИИ-менеджер в этом репозитории не используется")
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Storage(Path(self.tmp.name) / "s.db")
        self.notes = []

        async def notify(t, chat):
            self.notes.append((t, chat))
        self.notify = notify

    def tearDown(self):
        self.tmp.cleanup()

    def brain(self, script):
        from sales_brain import SalesBrain
        self.llm = FakeLLM(script)
        return SalesBrain(self.db, "Константин", notify=self.notify, completion=self.llm)

    def test_personal_message_is_ignored(self):
        b = self.brain([{"tool": "not_business", "args": {"reason": "мама спрашивает про ужин"}}, {"content": "-"}])
        self.assertIsNone(run(b.handle("tg:10", "Сынок, ты придёшь на ужин?")))
        self.assertTrue(self.db.get_state("tg:10")["ignored"])

    def test_handoff_notifies_owner(self):
        b = self.brain([
            {"tool": "handoff_to_owner", "args": {"reason": "хочет скидку 50 %", "summary": "A4 весь город 12 мес"}},
            {"content": "Это решает Константин лично — он напишет вам сегодня."},
        ])
        reply = run(b.handle("tg:11", "Дайте скидку 50 % и договоримся", who="Иван"))
        self.assertIn("сегодня", reply)
        self.assertIn("скидку 50", self.notes[0][0])
        self.assertEqual(self.notes[0][1], "tg:11")

    def test_prompt_rules(self):
        b = self.brain([{"content": "Здравствуйте! Подскажите, какой у вас бизнес?"}])
        run(b.handle("tg:12", "Здравствуйте, интересует реклама"))
        sysmsg = self.llm.calls[0]["messages"][0]["content"]
        self.assertIn("Никогда не ври", sysmsg)
        self.assertIn("Никаких скидок", sysmsg)
        self.assertIn("A4 200 ₽", sysmsg)

    def test_policy(self):
        from sales_policy import decide, is_repeated_spam
        base = dict(mode="non_contacts", is_contact=False, is_bot=False, user_id=5, allow=[], block=[],
                    state={}, replies_last_hour=0)
        self.assertTrue(decide(**base)[0])
        self.assertFalse(decide(**base | {"is_contact": True})[0])            # родные и друзья
        self.assertTrue(decide(**base | {"is_contact": True, "allow": [5]})[0])
        self.assertFalse(decide(**base | {"block": [5], "allow": [5]})[0])
        self.assertFalse(decide(**base | {"mode": "off"})[0])
        self.assertFalse(decide(**base | {"state": {"paused_until": time.time() + 60}})[0])
        self.assertFalse(decide(**base | {"replies_last_hour": 15})[0])
        self.assertFalse(decide(**base | {"state": {"ignored": True}})[0])
        hist = [{"role": "user", "content": "купи"}, {"role": "assistant", "content": "?"}, {"role": "user", "content": "купи"}]
        self.assertTrue(is_repeated_spam(hist, "купи"))
        self.assertFalse(is_repeated_spam(hist, "другое"))


if __name__ == "__main__":
    unittest.main()
