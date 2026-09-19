# Neura Lead Demo Bot

Универсальный демо-бот для 7 ниш: недвижимость, стоматология, салон красоты, автосервис, фитнес, ресторан, онлайн-школа.

## Что умеет

- Клиент выбирает нишу → бот превращается в ИИ-консультанта этой сферы
- Квалификация клиента через кнопки (2–3 вопроса)
- Свободный диалог с ИИ по каталогу и базе знаний
- Автосбор лидов (телефон) + уведомление владельцу
- Команда `/niche` — сменить нишу в любой момент

## Быстрый старт

```bash
pip install -r requirements.txt
cp .env.example .env
# Заполните .env своими ключами
python bot.py
```

## Переменные окружения

| Переменная | Описание |
|---|---|
| `BOT_TOKEN` | Токен от @BotFather — **обязательно** |
| `ADMIN_CHAT_ID` | Куда слать лиды (ID чата/канала) |
| `DEEPSEEK_API_KEY` | OpenRouter API ключ (основной мозг) |
| `YANDEX_API_KEY` + `YANDEX_FOLDER_ID` | YandexGPT (страховка) |
| `GIGACHAT_AUTH_KEY` | GigaChat (опционально) |
| `WEBHOOK_URL` | Для Render/Railway; без него — polling |

## Деплой

**Bothost / локально (polling):**
```bash
python bot.py
```

**Render / Railway (webhook):**
- Добавьте все переменные из `.env.example` в Environment Variables
- Установите `WEBHOOK_URL=https://your-app.onrender.com`
- Start command: `python bot.py`

## Сайт (GitHub Pages)

Лендинг (`index.html` + страницы ниш) публикуется через **GitHub Pages** прямо из этого репозитория
(Settings → Pages → Deploy from a branch, папка `/`). Файл `.nojekyll` отключает обработку Jekyll.

Адрес без домена: `https://kosvip369-pixel.github.io/neuralead-demo-bot/`

### Подключить домен neuralead.ru

1. Убедиться, что домен зарегистрирован и продлён у регистратора.
2. В DNS домена добавить записи:
   - `A @ 185.199.108.153`, `A @ 185.199.109.153`, `A @ 185.199.110.153`, `A @ 185.199.111.153`
   - `CNAME www kosvip369-pixel.github.io`
3. Создать в корне репозитория файл `CNAME` с одной строкой: `neuralead.ru`
   (или указать домен в Settings → Pages → Custom domain — GitHub создаст файл сам).
4. Через 10–60 минут включить **Enforce HTTPS** в Settings → Pages.

## Стоимость

Кнопочный бот — от 15 000 ₽ | ИИ-бот — от 50 000 ₽  
📞 +7 920 698-08-58
