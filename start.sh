#!/bin/bash
# NeuraSite AI (генератор сайтов) + демо-бот «Наш дом. Медиа» × NeuraLead (Telegram + MAX)

if [ -n "$POLZA_API_KEY" ] || [ -n "$DEEPSEEK_API_KEY" ]; then
  echo "🚀 Генератор сайтов на порту ${PORT:-8000}"
  python generator_server.py &
fi

# Telegram и MAX работают в ОДНОМ процессе — без двойных ответов
if [ -n "$BOT_TOKEN" ] || [ -n "$MAX_BOT_TOKEN" ]; then
  echo "🤖 Демо-бот (Telegram/MAX)"
  python run_bots.py &
fi

wait
