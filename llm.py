"""
Обращение к ИИ через Polza AI (OpenAI-совместимый API) с запасными моделями и инструментами.

Переменные окружения:
  POLZA_API_KEY   — ключ Polza (обязательно)
  POLZA_BASE_URL  — по умолчанию https://polza.ai/api/v1
  LLM_MODELS      — модели через запятую, первая основная, остальные запасные
"""

from __future__ import annotations

import io
import json
import logging
import os
from typing import Awaitable, Callable

log = logging.getLogger("llm")

POLZA_API_KEY = os.getenv("POLZA_API_KEY") or os.getenv("DEEPSEEK_API_KEY", "")
POLZA_BASE_URL = os.getenv("POLZA_BASE_URL") or os.getenv("LLM_BASE_URL") or "https://polza.ai/api/v1"
LLM_MODELS = [m.strip() for m in os.getenv(
    "LLM_MODELS", "google/gemini-2.5-flash,deepseek/deepseek-v4.1-flash,anthropic/claude-haiku-5.5"
).split(",") if m.strip()]
STT_MODEL = os.getenv("STT_MODEL", "openai/whisper-1")

ToolHandler = Callable[[dict], Awaitable[dict] | dict]

_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import AsyncOpenAI  # импорт здесь, чтобы тесты работали без библиотеки
        _client = AsyncOpenAI(api_key=POLZA_API_KEY or "none", base_url=POLZA_BASE_URL)
    return _client


async def _create(model: str, messages: list, tools: list | None):
    kwargs = dict(model=model, messages=messages, temperature=0.5, max_tokens=700)
    if tools:
        kwargs["tools"] = tools
    return await _get_client().chat.completions.create(**kwargs)


async def default_completion(messages: list, tools: list | None) -> dict:
    """Вызов модели с перебором запасных. Возвращает {'content': str, 'tool_calls': [...]}"""
    last_err = None
    for model in LLM_MODELS:
        for use_tools in ((True, False) if tools else (False,)):
            try:
                resp = await _create(model, messages, tools if use_tools else None)
                msg = resp.choices[0].message
                calls = []
                for tc in (msg.tool_calls or []):
                    calls.append({"id": tc.id, "name": tc.function.name, "arguments": tc.function.arguments or "{}"})
                return {"content": (msg.content or "").strip(), "tool_calls": calls, "model": model}
            except Exception as e:  # модель недоступна или не умеет инструменты — пробуем дальше
                last_err = e
                log.warning("Модель %s (tools=%s) недоступна: %s", model, use_tools, e)
    raise RuntimeError(f"Все модели недоступны: {last_err}")


async def run_agent(system: str, history: list[dict], tools: list | None = None,
                    handlers: dict[str, ToolHandler] | None = None,
                    completion=default_completion, max_steps: int = 4) -> tuple[str, list[dict]]:
    """
    Диалог с моделью с поддержкой инструментов.
    Возвращает (текст ответа, список выполненных инструментов [{name, args, result}]).
    """
    handlers = handlers or {}
    messages = [{"role": "system", "content": system}, *history]
    done: list[dict] = []
    for _ in range(max_steps):
        out = await completion(messages, tools)
        calls = out.get("tool_calls") or []
        if not calls:
            return out.get("content", ""), done
        messages.append({"role": "assistant", "content": out.get("content") or "",
                         "tool_calls": [{"id": c["id"], "type": "function",
                                         "function": {"name": c["name"], "arguments": c["arguments"]}} for c in calls]})
        for c in calls:
            try:
                args = json.loads(c["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            h = handlers.get(c["name"])
            if h is None:
                result = {"error": f"нет инструмента {c['name']}"}
            else:
                result = h(args)
                if hasattr(result, "__await__"):
                    result = await result
            done.append({"name": c["name"], "args": args, "result": result})
            messages.append({"role": "tool", "tool_call_id": c["id"], "content": json.dumps(result, ensure_ascii=False)})
    # слишком много шагов — просим ответить без инструментов
    out = await completion(messages, None)
    return out.get("content", ""), done


async def transcribe(audio: bytes, filename: str = "voice.ogg") -> str:
    f = io.BytesIO(audio)
    f.name = filename
    resp = await _get_client().audio.transcriptions.create(model=STT_MODEL, file=f, language="ru")
    return (resp.text or "").strip()
