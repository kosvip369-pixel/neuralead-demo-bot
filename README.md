# NeuraSite AI — Генератор сайтов на Polza AI 🚀

> **Опиши идею → получи готовый премиум сайт за 30 секунд. С чат-доработкой, генерацией картинок и анимациями.**

![NeuraSite](https://img.shields.io/badge/NeuraSite-AI%20Generator-6C5CFF?style=for-the-badge)
![Polza AI](https://img.shields.io/badge/Powered%20by-Polza%20AI-00D9FF?style=for-the-badge)
![Models](https://img.shields.io/badge/400%2B%20models-OpenAI%20%7C%20Claude%20%7C%20Gemini-FF4D8D?style=flat-square)

**Демо:** открой `index.html` или https://kosvip369-pixel.github.io/neuralead-demo-bot/

---

## ✨ Что умеет

### 🎨 Генерация сайтов
- **Опиши текстом** какой сайт нужен → AI генерирует полный HTML/CSS/JS
- **Форма контактов**: название, ниша, тип сайта, стиль, цвета, телефон, email, соцсети
- **Премиум дизайн** уровня Stripe, Linear, Vercel — не шаблонный
- **Анимации**: GSAP, parallax, fade-up, hover, floating — всё включено
- **Адаптив**: desktop / tablet / mobile превью
- **Один файл**: готовый сайт в одном HTML, открыл и работает

### 💬 Чат-доработка
- Не нравится? Напиши в чате: *«сделай темнее», «добавь отзывы», «поменяй цвета на золото»*
- AI мгновенно переписывает сайт, сохраняет всё остальное
- История генераций, быстрый откат

### 🖼 Картинки и генерация
- **Поиск**: Unsplash по запросу (business, coffee, medical...)
- **Генерация**: через Polza AI — Seedream 4.5, Flux 2 Pro, GPT Image 1.5
- Вставка в сайт одним кликом

### 📦 Экспорт
- Скачать HTML, копировать код, открыть в новой вкладке
- Готов к деплою на GitHub Pages, Vercel, Netlify

---

## 🧠 Мозги Polza AI — рекомендации

**Polza AI** — агрегатор №1 в РФ: 400+ моделей в одном API, оплата в рублях, без VPN.

| Задача | Модель | Почему | Цена |
|--------|--------|--------|------|
| **Генерация сайтов** | `anthropic/claude-sonnet-4-5` | 🔥 Лучший для фронтенда, понимает дизайн, пишет чистый Tailwind + GSAP | ~$3/1M |
| **Сложные SaaS** | `openai/gpt-5` | 💎 Премиум логика, большие проекты | ~$5/1M |
| **Креатив** | `google/gemini-2.5-pro` | 🎨 1M контекст, креатив, мультимодальность | ~$2.5/1M |
| **Быстро/дешево** | `deepseek/deepseek-v3.2` | ⚡ Лендинги за копейки | ~$0.5/1M |
| **Бесплатно** | `qwen/qwen3-235b-a22b:free` | 🆓 Русский, простые сайты | FREE |
| **Чат-правки** | `anthropic/claude-haiku-4-5` | 💬 Быстрый, дешевый для доработок | ~$1/1M |
| **Картинки фото** | `bytedance/seedream-4.5` | 🔥 Фотореализм топ | ~$0.05/img |
| **Иконки** | `openai/gpt-image-1.5` | 🎯 Точность, иконки | ~$0.08/img |
| **Фоны** | `black-forest-labs/flux-2-pro` | ⚡ Быстро, фоны | ~$0.03/img |
| **Видео hero** | `bytedance/seedance-2.5` | 🎬 Видео для hero | ~18₽/sec |

**Лучшая связка для генератора:**
```
Генерация → claude-sonnet-4-5
Правки в чате → claude-haiku-4-5
Картинки → seedream-4.5
Видео фон → seedance-2.5
```

Полный список: https://polza.ai/models и файл `polza_models.json`

---

## 🚀 Быстрый старт

### Вариант 1: GitHub Pages (без бекенда, самый простой)

1. Форкни репо
2. Включи GitHub Pages: Settings → Pages → Deploy from branch → `main` / root
3. Открой `https://твой-ник.github.io/neuralead-demo-bot/`
4. Вставь **Polza API ключ** в шапке (получить: https://polza.ai/register)
5. Генерируй!

> Frontend напрямую ходит в `https://polza.ai/api/v1` — работает без сервера.

### Вариант 2: Локально с бекендом (рекомендуется)

```bash
git clone https://github.com/kosvip369-pixel/neuralead-demo-bot.git
cd neuralead-demo-bot
pip install -r requirements.txt

# Укажи ключ
export POLZA_API_KEY=sk-polza-... 
# или создай .env из .env.example

python generator_server.py
# Открой http://localhost:8000
```

### Вариант 3: Docker / Render / Railway

```bash
# Dockerfile уже есть
docker build -t neurasite .
docker run -p 8000:8000 -e POLZA_API_KEY=... neurasite
```

Для Render/Railway:
- Start command: `python generator_server.py`
- Env: `POLZA_API_KEY`, `PORT=8000`

---

## 🔧 Как работает

```
[Форма: название, ниша, промпт, стиль, цвета, контакты]
        ↓
[System Prompt: элитный дизайнер Apple/Stripe/Linear + Tailwind + GSAP]
        ↓
[Polza AI → claude-sonnet-4-5 → генерирует HTML]
        ↓
[Preview iframe + Code view]
        ↓
[Чат: "сделай темнее" → claude-haiku-4-5 → обновляет HTML]
        ↓
[Экспорт: скачать / копировать / деплой]
```

**Промпт для генерации** (`generator_server.py`):
- Требует один файл, Tailwind CDN, GSAP, Unsplash картинки, анимации, адаптив, glassmorphism где уместно
- Стили: minimalism, glassmorphism, luxury, brutalism, cyberpunk, corporate...

**Промпт для доработки**: сохраняет структуру, точечно меняет по запросу.

---

## 📁 Структура

```
index.html              ← ГЛАВНЫЙ ГЕНЕРАТОР (SPA, работает на GitHub Pages)
generator.html          ← копия для /generator
generator_server.py     ← FastAPI бекенд + Polza proxy (/api/generate, /api/refine, /api/generate-image)
polza_models.json       ← рекомендации по моделям Polza AI
old-landing.html        ← старый лендинг NeuraLead
bot.py / bot_max.py     ← старые Telegram боты (сохранены)
requirements.txt
.env.example
```

---

## 🔑 Polza AI API

Получить ключ: https://polza.ai/register → Dashboard → API Keys

```python
from openai import OpenAI

client = OpenAI(
  base_url="https://polza.ai/api/v1",
  api_key="sk-polza-..."
)

# Генерация сайта
resp = client.chat.completions.create(
  model="anthropic/claude-sonnet-4-5",
  messages=[
    {"role": "system", "content": "Ты элитный веб-дизайнер..."},
    {"role": "user", "content": "Создай лендинг для кофейни..."}
  ]
)
print(resp.choices[0].message.content)

# Генерация картинки
img = client.images.generate(
  model="bytedance/seedream-4.5",
  prompt="futuristic coffee shop, minimal",
  size="1024x1024"
)
print(img.data[0].url)
```

Доки: https://polza.ai/docs

---

## 🎯 Примеры промптов

**Кофейня:**
> Лендинг для specialty кофейни, уютный теплый минимализм, много фото кофе, меню, история, адрес с картой

**SaaS:**
> SaaS продукт для управления задачами, как Linear, темный tech, градиенты, 6 фич, 3 тарифа, вау-анимации

**Клиника:**
> Клиника эстетической медицины, светлый премиум, доверие, услуги, врачи, до/после, отзывы

**Портфолио:**
> Портфолио фотографа, минимализм, большие фото, сетка, темный luxury

---

## 🤖 Старый функционал: NeuraLead Bot

В репо сохранены Telegram боты для 12 ниш (недвижимость, стоматология, салон и т.д.):

```bash
pip install -r requirements.txt
export BOT_TOKEN=...
python bot.py
```

Демо: https://t.me/Konstantin2323_bot

---

## 📄 Лицензия

MIT. Делай что хочешь, но укажи Polza AI как провайдера мозгов 😉

---

**Сделано с ❤️ на Polza AI**

- Polza: https://polza.ai/
- Модели: https://polza.ai/models
- Доки: https://polza.ai/docs
- ТГ канал: https://t.me/polzaai

Вопросы? Пиши в Issues или +7 920 698-08-58
