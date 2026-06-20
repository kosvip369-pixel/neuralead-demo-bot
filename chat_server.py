"""
Простой HTTP-сервер для виджета чата.
Принимает POST /chat, проксирует к OpenRouter.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
PORT = int(os.environ.get("PORT", 8000))

SYSTEM_PROMPTS = {
    "dental": "Ты — Константин, консультант стоматологии. Помогаешь записаться на приём, отвечаешь на вопросы о процедурах и ценах. Пиши кратко (2-4 строки), по-человечески, с 1-2 эмодзи. Не раскрывай что ты AI.",
    "clinic": "Ты — Константин, консультант медицинской клиники. Помогаешь выбрать врача, записаться на приём. Пиши кратко (2-4 строки), по-человечески. Не раскрывай что ты AI.",
    "salon": "Ты — Константин, консультант салона красоты. Помогаешь записаться к мастеру, отвечаешь о ценах. Пиши кратко (2-4 строки), дружелюбно. Не раскрывай что ты AI.",
    "fitness": "Ты — Константин, консультант фитнес-клуба. Помогаешь записаться на пробное, рассказываешь об абонементах. Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    "autoservice": "Ты — Константин, консультант автосервиса. Помогаешь записаться на ТО, отвечаешь о ценах. Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    "detailing": "Ты — Константин, консультант детейлинг-центра. Помогаешь выбрать услугу (полировка, керамика, химчистка). Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    "realty": "Ты — Константин, консультант агентства недвижимости. Помогаешь с подбором жилья, записываешь на просмотр. Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    "horeca": "Ты — Константин, консультант ресторана/отеля. Помогаешь забронировать стол или номер. Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    "education": "Ты — Константин, консультант онлайн-школы. Помогаешь выбрать курс, записываешь на пробный урок. Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    "hr": "Ты — Константин, HR-консультант. Помогаешь кандидатам с вакансиями, записываешь на собеседование. Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    "finance": "Ты — Константин, финансовый консультант. Помогаешь с вопросами по страхованию и кредитам. Пиши кратко (2-4 строки). Не раскрывай что ты AI.",
    "default": "Ты — Константин, консультант NueraLead. Помогаешь посетителям сайта: отвечаешь на вопросы о чат-ботах, ценах и внедрении. Пиши кратко (2-4 строки), по-человечески, с 1-2 эмодзи. Не раскрывай что ты AI.",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # отключаем лишние логи

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/chat":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length))
        except Exception:
            self._json(400, {"error": "Invalid JSON"})
            return

        messages = body.get("messages", [])
        niche = body.get("niche", "default")
        system = SYSTEM_PROMPTS.get(niche, SYSTEM_PROMPTS["default"])

        if not OPENROUTER_API_KEY:
            self._json(500, {"error": "OPENROUTER_API_KEY not set"})
            return

        try:
            resp = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://neuralead-demo.netlify.app",
                    "X-Title": "NueraLead Chat Widget",
                },
                json={
                    "model": "deepseek/deepseek-chat-v3-0324:free",
                    "messages": [{"role": "system", "content": system}] + messages,
                    "max_tokens": 300,
                    "temperature": 0.7,
                },
                timeout=30,
            )
            data = resp.json()
            reply = data["choices"][0]["message"]["content"]
            self._json(200, {"reply": reply})
        except Exception as e:
            self._json(502, {"error": str(e)})

    def _json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self._cors()
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Chat server running on port {PORT}")
    server.serve_forever()
