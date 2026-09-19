# 🔑 Куда вставить ключи Polza AI — подробная инструкция

## Получить ключ

1. Иди на https://polza.ai/register
2. Зарегистрируйся (почта + пароль, 30 сек)
3. Пополни баланс: Dashboard → Пополнить → 100-300₽ (хватит на 20-30 сайтов, оплата российской картой)
4. Dashboard → API Keys → Create Key → скопируй `sk-polza-...` (начинается с `sk-`)

---

## Вариант 1: GitHub Pages / Статика (самый простой, без сервера)

**Где вставлять:** прямо в браузере, в шапке генератора.

### Шаги:
1. Открой генератор: `https://твой-ник.github.io/neuralead-demo-bot/` или локально `index.html`
2. Вверху справа найди поле:
   ```
   [●] [ 🔑 Polza API ключ (sk-polza-...) ] [👁] [OK] [Model ▼] [Получить ключ] [🧠 Мозги]
   ```
3. Вставь ключ `sk-polza-...` и нажми **OK**
4. Индикатор станет зеленым `●` — ключ сохранен в `localStorage`
5. Можешь генерировать!

**Мобильная версия:** поле внизу шапки, там же.

**Если не вставил:** появится баннер сверху:
> 🔑 Нужен Polza API ключ — без него генерация не работает. Вставь ключ в поле выше ↑

И модалка "Где взять ключ?" с инструкцией.

**Безопасность:** ключ хранится только у тебя в браузере, отправляется только на `https://polza.ai/api/v1`. Для продакшена лучше бекенд.

---

## Вариант 2: Локальный запуск с бекендом (рекомендуется)

**Где вставлять:** в файл `.env` или переменную окружения.

### Шаги:

```bash
git clone https://github.com/kosvip369-pixel/neuralead-demo-bot.git
cd neuralead-demo-bot
pip install -r requirements.txt

# Способ A: через .env файл
cp .env.example .env
# Открой .env в редакторе (nano .env или VS Code)
# Найди строку:
# POLZA_API_KEY=sk-polza-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
# Замени на свой ключ:
# POLZA_API_KEY=sk-polza-твой-реальный-ключ

# Способ B: через переменную окружения (без файла)
export POLZA_API_KEY=sk-polza-твой-ключ
export POLZA_BASE_URL=https://polza.ai/api/v1
export PORT=8000

# Запусти
python generator_server.py
# Открой http://localhost:8000
```

Теперь ключ в браузере указывать **не нужно** — бекенд сам проксирует запросы к Polza AI и скрывает ключ.

**Проверка:**
```bash
curl http://localhost:8000/health
# {"status":"ok","polza_configured":true,"base_url":"https://polza.ai/api/v1"}
```

---

## Вариант 3: Деплой на Render / Railway / VPS / Docker

### Render:
1. New Web Service → подключи GitHub репо
2. Build: `pip install -r requirements.txt`
3. Start: `python generator_server.py`
4. Environment → Add:
   ```
   POLZA_API_KEY=sk-polza-...
   POLZA_BASE_URL=https://polza.ai/api/v1
   PORT=8000
   ```
5. Deploy

### Railway:
1. New Project → Deploy from GitHub
2. Variables → Add `POLZA_API_KEY`
3. Deploy

### Docker:
```bash
docker build -t neurasite .
docker run -p 8000:8000 -e POLZA_API_KEY=sk-polza-... neurasite
```

### .env.example:
```env
POLZA_API_KEY=sk-polza-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
POLZA_BASE_URL=https://polza.ai/api/v1
POLZA_TEXT_MODEL=anthropic/claude-sonnet-4-5
POLZA_IMAGE_MODEL=bytedance/seedream-4.5
```

---

## Вариант 4: Для старых ботов (NeuraLead)

Если используешь Telegram ботов `bot.py`:

```env
BOT_TOKEN=123456:ABC...
ADMIN_CHAT_ID=123456789
DEEPSEEK_API_KEY=sk-polza-...  # можно использовать POLZA_API_KEY как DEEPSEEK_API_KEY
LLM_BASE_URL=https://polza.ai/api/v1
LLM_MODELS=anthropic/claude-sonnet-4-5,openai/gpt-5
```

Бот тоже работает через Polza AI.

---

## FAQ

**Вставил ключ, но пишет "Polza API error"?**
- Проверь баланс на https://polza.ai/dashboard — пополни если 0
- Проверь что ключ скопирован полностью, без пробелов, начинается с `sk-`
- Попробуй другую модель: в шапке выбери `deepseek/deepseek-v3.2` или `qwen/qwen3-235b-a22b:free` (бесплатная)

**Где ключ хранится в браузере?**
- DevTools → Application → Local Storage → `polza_key`
- Можешь удалить: `localStorage.removeItem('polza_key')` в консоли

**Можно ли использовать один ключ на всех?**
- Да, но лучше каждому свой. Один ключ = один баланс.

**Сколько стоит генерация?**
- Сайт: ~5-15₽ (Claude Sonnet 4.5)
- Картинка: ~3-8₽ (Seedream 4.5)
- На 300₽ — 20-30 сайтов.

**Безопасно ли вставлять ключ в GitHub Pages?**
- Для личных проектов — ок. Ключ виден только у тебя в браузере.
- Для продакшена/клиентов — используй бекенд `generator_server.py`, он скрывает ключ.

---

## Видео-инструкция (текст)

```
1. polza.ai/register → регистрация
2. Пополнить 100₽
3. API Keys → Create → Copy sk-polza-...
4. Открыть генератор → в шапке поле "🔑 Polza API ключ" → вставить → OK → зеленый индикатор ●
5. Заполнить форму слева → "Сгенерировать сайт"
6. Готово!
```

Если все еще не понятно — открой в генераторе кнопку **"Где взять ключ?"** (в баннере) — там все с картинками.
