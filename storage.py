"""
Хранилище на SQLite: история переписки, заявки, состояние чатов и настройки.
Файл базы лежит в папке DATA_DIR (по умолчанию ./data). На хостинге эту папку
нужно сделать постоянной (volume), иначе данные пропадут при обновлении.
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import time
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))


class Storage:
    def __init__(self, path: str | Path | None = None):
        if path is None:
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            path = DATA_DIR / "bot.sqlite3"
        self.path = str(path)
        self._lock = threading.Lock()
        self.db = sqlite3.connect(self.path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
            CREATE TABLE IF NOT EXISTS messages(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat TEXT NOT NULL, role TEXT NOT NULL, content TEXT NOT NULL, ts REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS messages_chat ON messages(chat, id);
            CREATE TABLE IF NOT EXISTS leads(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat TEXT NOT NULL, channel TEXT, name TEXT, phone TEXT, company TEXT,
                interest TEXT, summary TEXT, ts REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS chats(
                chat TEXT PRIMARY KEY, state TEXT NOT NULL DEFAULT '{}');
            CREATE TABLE IF NOT EXISTS settings(
                key TEXT PRIMARY KEY, value TEXT NOT NULL);
            """
        )
        self.db.commit()

    # ------------------------------------------------------------ история
    def add_message(self, chat: str, role: str, content: str) -> None:
        with self._lock:
            self.db.execute("INSERT INTO messages(chat, role, content, ts) VALUES(?,?,?,?)",
                            (chat, role, content, time.time()))
            self.db.commit()

    def history(self, chat: str, limit: int = 20) -> list[dict]:
        rows = self.db.execute(
            "SELECT role, content FROM messages WHERE chat=? ORDER BY id DESC LIMIT ?", (chat, limit)
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    def clear_history(self, chat: str) -> None:
        with self._lock:
            self.db.execute("DELETE FROM messages WHERE chat=?", (chat,))
            self.db.commit()

    def count_assistant_since(self, chat: str, since_ts: float) -> int:
        row = self.db.execute(
            "SELECT COUNT(*) AS n FROM messages WHERE chat=? AND role='assistant' AND ts>=?", (chat, since_ts)
        ).fetchone()
        return int(row["n"])

    # ------------------------------------------------------------ заявки
    def add_lead(self, chat: str, channel: str, name: str = "", phone: str = "", company: str = "",
                 interest: str = "", summary: str = "") -> int:
        with self._lock:
            cur = self.db.execute(
                "INSERT INTO leads(chat, channel, name, phone, company, interest, summary, ts) VALUES(?,?,?,?,?,?,?,?)",
                (chat, channel, name, phone, company, interest, summary, time.time()),
            )
            self.db.commit()
            return int(cur.lastrowid)

    def leads(self, limit: int = 10) -> list[dict]:
        rows = self.db.execute("SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def lead_exists(self, chat: str, phone: str) -> bool:
        row = self.db.execute("SELECT 1 FROM leads WHERE chat=? AND phone=? LIMIT 1", (chat, phone)).fetchone()
        return row is not None

    # ------------------------------------------------------------ состояние чата
    def get_state(self, chat: str) -> dict:
        row = self.db.execute("SELECT state FROM chats WHERE chat=?", (chat,)).fetchone()
        return json.loads(row["state"]) if row else {}

    def set_state(self, chat: str, **values) -> dict:
        state = self.get_state(chat)
        for k, v in values.items():
            if v is None:
                state.pop(k, None)
            else:
                state[k] = v
        with self._lock:
            self.db.execute("INSERT INTO chats(chat, state) VALUES(?,?) ON CONFLICT(chat) DO UPDATE SET state=excluded.state",
                            (chat, json.dumps(state, ensure_ascii=False)))
            self.db.commit()
        return state

    def is_known_chat(self, chat: str) -> bool:
        return self.db.execute("SELECT 1 FROM chats WHERE chat=?", (chat,)).fetchone() is not None

    # ------------------------------------------------------------ настройки
    def get_setting(self, key: str, default=None):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return json.loads(row["value"]) if row else default

    def set_setting(self, key: str, value) -> None:
        with self._lock:
            self.db.execute("INSERT INTO settings(key, value) VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                            (key, json.dumps(value, ensure_ascii=False)))
            self.db.commit()
