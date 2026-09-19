#!/bin/bash
# NeuraSite AI + NeuraLead Bots starter

# Если есть POLZA_API_KEY - запускаем генератор сайтов (основной)
if [ ! -z "$POLZA_API_KEY" ] || [ ! -z "$DEEPSEEK_API_KEY" ]; then
  echo "🚀 Starting NeuraSite AI Generator on port ${PORT:-8000}"
  python generator_server.py &
  GEN_PID=$!
fi

# Если есть BOT_TOKEN - запускаем ботов (совместимость)
if [ ! -z "$BOT_TOKEN" ]; then
  echo "🤖 Starting Telegram bots"
  python bot.py &
  BOT_PID=$!
  python bot_max.py &
  MAX_PID=$!
fi

# Если ничего не запустилось - запускаем генератор в любом случае
if [ -z "$GEN_PID" ] && [ -z "$BOT_PID" ]; then
  echo "⚠️ No keys found, starting generator anyway (needs key in UI)"
  python generator_server.py &
  GEN_PID=$!
fi

wait
