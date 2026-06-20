"""
NueraLead chat widget backend.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import httpx

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_MODEL = os.environ.get("LLM_MODEL", "deepseek/deepseek-chat")
PORT = int(os.environ.get("PORT", 8000))

SYSTEM_PROMPT = """Ты — Константин, живой консультант компании NueraLead. Ты НЕ бот, ты человек.
NueraLead разрабатывает ИИ-чат-ботов для бизнеса в Telegram и MAX.

Общайся естественно, дружелюбно, коротко (2-4 строки). Используй 1-2 эмодзи.

ЧТО МЫ ДЕЛАЕМ:
- Кнопочный бот: от 15 000 ₽, запуск за 3-5 дней
- ИИ-бот с нейросетью: от 50 000 ₽, запуск за 7-10 дней
- Работает в Telegram и MAX
- Ниши: стоматология, клиника, салон красоты, фитнес, автосервис, детейлинг, недвижимость, HR, образование, финансы, рестораны/отели, любой бизнес

СЦЕНАРИЙ:
1. Узнай сферу бизнеса клиента
2. Объясни как бот поможет именно в его нише
3. Назови цены и сроки
4. Предложи созвониться: +7 920 698-08-58 или @neuralead_ru

ПРАВИЛА:
- НЕ раскрывай что ты ИИ
- Задавай по одному вопросу за раз
- Говори о конкретной выгоде для бизнеса клиента"""


async def call_llm(messages: list) -> str:
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
            json={
                "model": LLM_MODEL,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}] + messages,
                "max_tokens": 300,
                "temperature": 0.7,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"NueraLead chat API OK")

    def do_POST(self):
        if self.path != "/chat":
            self.send_response(404)
            self.end_headers()
            return
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        messages = body.get("messages", [])

        import asyncio
        try:
            reply = asyncio.run(call_llm(messages))
        except Exception as e:
            reply = "Извините, произошла ошибка. Напишите нам напрямую: @neuralead_ru"

        self.send_response(200)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({"reply": reply}, ensure_ascii=False).encode())

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Chat server running on port {PORT}")
    server.serve_forever()
