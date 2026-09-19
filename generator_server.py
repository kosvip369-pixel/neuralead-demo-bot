"""
NeuraSite AI - Генератор сайтов на Polza AI
Backend: FastAPI + Polza AI proxy

Запуск:
pip install fastapi uvicorn openai httpx python-multipart
POLZA_API_KEY=... python generator_server.py
или
uvicorn generator_server:app --host 0.0.0.0 --port 8000 --reload
"""

import os
import json
import re
import asyncio
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import httpx
from openai import AsyncOpenAI

# ---------- Конфиг ----------
POLZA_API_KEY = os.environ.get("POLZA_API_KEY", "") or os.environ.get("DEEPSEEK_API_KEY", "")
POLZA_BASE_URL = os.environ.get("POLZA_BASE_URL", "https://polza.ai/api/v1")
PORT = int(os.environ.get("PORT", 8000))

# Модели по умолчанию - рекомендации с polza.ai
DEFAULT_TEXT_MODEL = "anthropic/claude-sonnet-4-5"  # Лучшая для фронтенда
DEFAULT_IMAGE_MODEL = "bytedance/seedream-4.5"
FALLBACK_MODELS = [
    "anthropic/claude-sonnet-4-5",
    "openai/gpt-5",
    "google/gemini-2.5-pro",
    "deepseek/deepseek-v3.2",
    "qwen/qwen3-235b-a22b:free",
]

# ---------- FastAPI ----------
app = FastAPI(title="NeuraSite AI Generator", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Polza Client ----------
def get_polza_client(api_key: Optional[str] = None):
    key = api_key or POLZA_API_KEY
    if not key:
        return None
    return AsyncOpenAI(api_key=key, base_url=POLZA_BASE_URL)

# ---------- System Prompts ----------
SITE_GENERATION_PROMPT = """Ты — элитный веб-дизайнер уровня Apple, Stripe, Linear, Vercel + senior frontend-разработчик.

Твоя задача: сгенерировать ОДИН ПОЛНЫЙ HTML файл сайта по запросу пользователя.

ТРЕБОВАНИЯ К КОДУ:
1. **Один файл**: весь HTML, CSS, JS внутри одного файла. Никаких внешних файлов кроме CDN.
2. **CDN разрешены**: 
   - Tailwind CSS: https://cdn.tailwindcss.com
   - Google Fonts (Inter, Manrope, Space Grotesk, JetBrains Mono)
   - Lucide Icons или Font Awesome
   - GSAP для анимаций: https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js + ScrollTrigger
   - AOS необязательно, лучше чистый IntersectionObserver + GSAP

3. **Дизайн уровня Dribbble Top 1%**:
   - Современный, чистый, дорогой вид
   - Glassmorphism, неоморфизм, градиенты, blur эффекты где уместно
   - Идеальная типографика: заголовки 48-72px, плотный трекинг
   - Микро-анимации на все интерактивные элементы
   - Скругления 16-24px, мягкие тени
   - Темная или светлая тема в зависимости от ниши, но всегда премиум

4. **Анимации ОБЯЗАТЕЛЬНО**:
   - Появление секций при скролле (fade-up, stagger)
   - Параллакс для hero
   - Hover эффекты с transform и transition
   - Плавный скролл
   - Анимированные градиенты, floating элементы
   - Кнопки с эффектом магнита или shine

5. **Картинки**:
   - Используй https://images.unsplash.com/photo-xxx?w=1200&h=800&fit=crop с релевантными запросами
   - Для бизнеса: подбери реальные фото по теме (например для ресторана - еда, интерьер)
   - Добавь alt тексты
   - Используй object-cover, aspect-ratio

6. **Структура сайта** (адаптируй под запрос):
   - Header с логотипом и навигацией (sticky, blur)
   - Hero с мощным заголовком, подзаголовком, CTA, визуалом
   - Преимущества / фичи (3-6 карточек)
   - О компании / продукт
   - Соцдоказательства (отзывы, цифры, логотипы)
   - Тарифы или каталог
   - FAQ
   - Контакты + форма + карта
   - Footer

7. **Интерактив**:
   - Мобильное меню
   - Форма с валидацией (имитация отправки)
   - FAQ аккордеон
   - Плавные якорные ссылки
   - Модалки если нужно

8. **Контакты**: используй данные которые дал пользователь. Если не дал - придумай реалистичные.

9. **Русский язык** по умолчанию, если не указано иное.

10. **Код должен быть рабочим сразу** - открываешь файл и все работает, без ошибок.

11. **НЕ ПИШИ** никаких объяснений, только HTML код. Начни с <!DOCTYPE html>

СТИЛИ:
- Если пользователь выбрал стиль, строго следуй ему:
  - Минимализм: много воздуха, ч/б, тонкие линии
  - Glassmorphism: полупрозрачность, backdrop-blur, градиенты
  - Неоморфизм: мягкие тени, выдавленные элементы
  - Брутализм: жирные шрифты, резкие углы, контраст
  - Luxury: золото, темный фон, serif шрифты
  - Cyberpunk: неон, темный, tech
  - Corporate: синий, чистый, доверительный
  - Startup: яркий, градиенты, дружелюбный

ФОРМАТ ОТВЕТА: Только HTML код, без markdown оберток, без ```html
"""

REFINE_PROMPT = """Ты — senior frontend-разработчик, который дорабатывает существующий сайт.

Тебе дают:
1. Текущий HTML код сайта
2. Запрос пользователя что исправить/улучшить

Твоя задача:
- Внимательно прочитать запрос
- Внести ТОЧЕЧНЫЕ изменения, сохранив всю остальную структуру и стиль
- Если просят добавить секцию - добавь красиво в подходящее место
- Если просят поменять цвета - поменяй везде согласованно
- Если просят анимации - добавь GSAP или CSS анимации
- Если просят картинки - замени src на более подходящие Unsplash URL

ПРАВИЛА:
1. Верни ПОЛНЫЙ обновленный HTML файл, не diff
2. Сохрани все что не просили менять
3. Код должен оставаться рабочим
4. Не ломай верстку
5. Улучшай, а не ухудшай дизайн
6. Только HTML, без объяснений, без markdown

Текущий HTML будет в сообщении пользователя после запроса.
"""

# ---------- Models ----------
class GenerateRequest(BaseModel):
    prompt: str
    site_name: Optional[str] = "NeuraSite"
    business_type: Optional[str] = ""
    site_type: Optional[str] = "landing"
    style: Optional[str] = "modern"
    colors: Optional[str] = ""
    contacts: Optional[Dict[str, str]] = None
    features: Optional[List[str]] = None
    model: Optional[str] = None
    api_key: Optional[str] = None

class RefineRequest(BaseModel):
    current_html: str
    message: str
    model: Optional[str] = None
    api_key: Optional[str] = None

class ImageGenRequest(BaseModel):
    prompt: str
    model: Optional[str] = None
    api_key: Optional[str] = None
    size: Optional[str] = "1024x1024"

class ImageSearchRequest(BaseModel):
    query: str
    count: Optional[int] = 6

# ---------- Helpers ----------
def build_generation_user_message(req: GenerateRequest) -> str:
    contacts_str = ""
    if req.contacts:
        contacts_str = "\n".join([f"- {k}: {v}" for k, v in req.contacts.items() if v])
    
    features_str = ", ".join(req.features) if req.features else "базовые"

    return f"""
ЗАДАЧА: Создай сайт

Название/Компания: {req.site_name}
Сфера: {req.business_type}
Тип сайта: {req.site_type}
Стиль дизайна: {req.style}
Цветовая схема: {req.colors or 'подбери сам премиум палитру под нишу'}
Фичи: {features_str}

Контакты:
{contacts_str or 'придумай реалистичные'}

Описание от пользователя:
{req.prompt}

СГЕНЕРИРУЙ ПОЛНЫЙ HTML ФАЙЛ СЕЙЧАС. Только код, без объяснений.
"""

async def call_polza_chat(messages: List[Dict], model: str, api_key: Optional[str] = None, temperature: float = 0.8, max_tokens: int = 16000) -> str:
    client = get_polza_client(api_key)
    if not client:
        raise HTTPException(status_code=400, detail="POLZA_API_KEY не установлен. Укажите ключ в .env или в запросе.")
    
    # Попробуем каскад моделей если основная не сработала
    models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]
    
    last_error = None
    for m in models_to_try[:3]:  # пробуем 3 модели
        try:
            resp = await client.chat.completions.create(
                model=m,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            content = resp.choices[0].message.content
            # Очистим от markdown если есть
            content = re.sub(r'^```html\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'^```\s*', '', content, flags=re.MULTILINE)
            content = re.sub(r'\s*```$', '', content, flags=re.MULTILINE)
            return content.strip()
        except Exception as e:
            last_error = str(e)
            print(f"Model {m} failed: {e}")
            continue
    
    raise HTTPException(status_code=500, detail=f"Все модели упали. Последняя ошибка: {last_error}")

# ---------- Routes ----------
@app.get("/health")
async def health():
    return {"status": "ok", "polza_configured": bool(POLZA_API_KEY), "base_url": POLZA_BASE_URL}

@app.get("/api/models")
async def get_models():
    """Рекомендованные модели с Polza AI"""
    return {
        "text_models": [
            {
                "id": "anthropic/claude-sonnet-4-5",
                "name": "Claude Sonnet 4.5",
                "best_for": "Фронтенд, дизайн, код - ЛУЧШИЙ ВЫБОР",
                "price": "~$3 / 1M токенов",
                "context": "200k",
                "badge": "🔥 Рекомендуем"
            },
            {
                "id": "openai/gpt-5",
                "name": "GPT-5",
                "best_for": "Сложные SaaS, логика, большие сайты",
                "price": "~$5 / 1M",
                "context": "400k",
                "badge": "💎 Премиум"
            },
            {
                "id": "google/gemini-2.5-pro",
                "name": "Gemini 2.5 Pro",
                "best_for": "Креатив, длинный контекст, мультимодальность",
                "price": "~$2.5 / 1M",
                "context": "1M",
                "badge": "🎨 Креатив"
            },
            {
                "id": "deepseek/deepseek-v3.2",
                "name": "DeepSeek V3.2",
                "best_for": "Быстро и дешево, хорошее качество",
                "price": "~$0.5 / 1M",
                "context": "128k",
                "badge": "⚡ Быстро"
            },
            {
                "id": "qwen/qwen3-235b-a22b:free",
                "name": "Qwen3 235B",
                "best_for": "Бесплатно, русский язык, лендинги",
                "price": "FREE",
                "context": "32k",
                "badge": "🆓 Бесплатно"
            },
            {
                "id": "anthropic/claude-haiku-4-5",
                "name": "Claude Haiku 4.5",
                "best_for": "Доработки в чате, быстрые правки",
                "price": "~$1 / 1M",
                "context": "200k",
                "badge": "💬 Для чата"
            }
        ],
        "image_models": [
            {
                "id": "bytedance/seedream-4.5",
                "name": "Seedream 4.5",
                "best_for": "Фотореализм, лучший общий",
                "price": "~$0.05 / image",
                "badge": "🔥 Топ"
            },
            {
                "id": "openai/gpt-image-1.5",
                "name": "GPT Image 1.5",
                "best_for": "Иконки, иллюстрации, точность",
                "price": "~$0.08 / image",
                "badge": "🎯 Точность"
            },
            {
                "id": "black-forest-labs/flux-2-pro",
                "name": "Flux 2 Pro",
                "best_for": "Фоны, быстро, дешево",
                "price": "~$0.03 / image",
                "badge": "⚡ Быстро"
            },
            {
                "id": "google/nano-banana-pro",
                "name": "Nano Banana Pro",
                "best_for": "Редактирование, ретушь",
                "price": "~$0.04 / image",
                "badge": "✏️ Редактор"
            }
        ],
        "video_models": [
            {
                "id": "bytedance/seedance-2.5",
                "name": "Seedance 2.5",
                "best_for": "Видео для hero, лучший",
                "price": "~$0.20 / sec",
                "badge": "🔥 Видео топ"
            },
            {
                "id": "kuaishou/kling-3.0",
                "name": "Kling 3.0",
                "best_for": "Кинематографичность",
                "price": "~$0.15 / sec",
                "badge": "🎬 Кино"
            },
            {
                "id": "alibaba/wan-3.0",
                "name": "Wan 3.0",
                "best_for": "Моушн графика",
                "price": "~$0.12 / sec",
                "badge": "✨ Моушн"
            },
            {
                "id": "google/veo-3.1",
                "name": "Veo 3.1",
                "best_for": "Максимальное качество",
                "price": "~$0.30 / sec",
                "badge": "💎 Премиум"
            }
        ]
    }

@app.post("/api/generate")
async def generate_site(req: GenerateRequest):
    model = req.model or DEFAULT_TEXT_MODEL
    
    messages = [
        {"role": "system", "content": SITE_GENERATION_PROMPT},
        {"role": "user", "content": build_generation_user_message(req)}
    ]
    
    try:
        html = await call_polza_chat(messages, model, req.api_key, temperature=0.85, max_tokens=16000)
        
        # Проверка что это HTML
        if "<!DOCTYPE" not in html and "<html" not in html:
            # Попробуем извлечь HTML из текста
            match = re.search(r'<!DOCTYPE.*</html>', html, re.DOTALL | re.IGNORECASE)
            if match:
                html = match.group(0)
        
        return {"html": html, "model_used": model}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/refine")
async def refine_site(req: RefineRequest):
    model = req.model or "anthropic/claude-haiku-4-5"  # для доработок быстрая модель
    
    # Ограничим размер HTML для контекста (если слишком большой - обрежем)
    html_to_send = req.current_html
    if len(html_to_send) > 80000:
        # Оставим начало и конец, вырежем середину с пометкой
        html_to_send = html_to_send[:40000] + "\n\n<!-- ... СЕРЕДИНА САЙТА СОКРАЩЕНА ДЛЯ ЭКОНОМИИ КОНТЕКСТА, НО ТЫ ДОЛЖЕН СОХРАНИТЬ ЕЕ ... -->\n\n" + html_to_send[-40000:]
    
    messages = [
        {"role": "system", "content": REFINE_PROMPT},
        {"role": "user", "content": f"Запрос на доработку: {req.message}\n\nТекущий HTML:\n{html_to_send}\n\nВерни ПОЛНЫЙ обновленный HTML."}
    ]
    
    try:
        html = await call_polza_chat(messages, model, req.api_key, temperature=0.7, max_tokens=16000)
        return {"html": html, "model_used": model}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-image")
async def generate_image(req: ImageGenRequest):
    client = get_polza_client(req.api_key)
    if not client:
        raise HTTPException(status_code=400, detail="POLZA_API_KEY не установлен")
    
    model = req.model or DEFAULT_IMAGE_MODEL
    
    try:
        # Polza использует OpenAI-совместимый API для изображений
        resp = await client.images.generate(
            model=model,
            prompt=req.prompt,
            size=req.size,
            n=1
        )
        # В зависимости от провайдера ответ может быть url или b64
        image_url = resp.data[0].url if hasattr(resp.data[0], 'url') and resp.data[0].url else None
        b64 = resp.data[0].b64_json if hasattr(resp.data[0], 'b64_json') and resp.data[0].b64_json else None
        
        return {"url": image_url, "b64": b64, "model": model}
    except Exception as e:
        # Fallback - вернем Unsplash URL по промпту
        fallback_url = f"https://images.unsplash.com/photo-1550745165-9bc0b252726f?w=1024&h=1024&fit=crop&q=80"
        print(f"Image gen failed {model}: {e}, fallback to unsplash")
        # Попробуем через чат-модель сгенерить поисковый запрос для unsplash
        return {"url": fallback_url, "error": str(e), "fallback": True}

@app.post("/api/search-images")
async def search_images(req: ImageSearchRequest):
    """Поиск картинок - используем Unsplash Source + Picsum как фолбек, без ключа"""
    query = req.query.strip()
    # Формируем Unsplash URL - они работают без ключа для демо
    # Используем source.unsplash.com альтернативу через unsplash.com/photos/random?query
    images = []
    # Генерим разные URL с рандомизацией
    base_queries = [query, f"{query} business", f"{query} minimal", f"{query} aesthetic"]
    
    for i in range(req.count):
        q = base_queries[i % len(base_queries)]
        # Используем picsum + unsplash
        if i % 2 == 0:
            # Unsplash with query
            encoded = q.replace(" ", ",")
            url = f"https://images.unsplash.com/photo-{1550000000000 + i*12345}?w=800&h=600&fit=crop&q=80&auto=format"  # placeholder, заменим на рабочий поиск
            # Реально рабочие unsplash фото по темам - маппинг
            url = f"https://source.unsplash.com/800x600/?{encoded}&sig={i}"
            # source.unsplash.com deprecated, используем unsplash api proxy через images.unsplash.com с поиском
            # Лучше использовать lorem picsum + unsplash collection
            url = f"https://picsum.photos/seed/{hash(q+str(i)) % 10000}/800/600"
        else:
            # Unsplash direct - используем известные фото ID для разных тем
            topic_map = {
                "business": "https://images.unsplash.com/photo-1497366216548-37526070297c?w=800&h=600&fit=crop",
                "restaurant": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=800&h=600&fit=crop",
                "tech": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&h=600&fit=crop",
                "medical": "https://images.unsplash.com/photo-1576091160550-2173dba999ef?w=800&h=600&fit=crop",
                "fitness": "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800&h=600&fit=crop",
                "beauty": "https://images.unsplash.com/photo-1560066984-138dadb4c035?w=800&h=600&fit=crop",
                "realty": "https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=800&h=600&fit=crop",
                "education": "https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=800&h=600&fit=crop",
            }
            # найдем ближайшее
            found = None
            for k, v in topic_map.items():
                if k in q.lower():
                    found = v
                    break
            url = found or f"https://images.unsplash.com/photo-1506744038136-46273834b3fb?w=800&h=600&fit=crop&ixid={i}"

        images.append({
            "url": url,
            "query": q,
            "source": "unsplash"
        })
    
    # Добавим реальные unsplash URL для популярных запросов - чтобы точно работало
    real_images = [
        f"https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=800&h=600&fit=crop",
        f"https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=600&fit=crop",
        f"https://images.unsplash.com/photo-1553877522-43269d4ea984?w=800&h=600&fit=crop",
        f"https://images.unsplash.com/photo-1558655146-d09347e92766?w=800&h=600&fit=crop",
        f"https://images.unsplash.com/photo-1551434678-e076c223a692?w=800&h=600&fit=crop",
        f"https://images.unsplash.com/photo-1542744173-8e7e53415bb4?w=800&h=600&fit=crop",
    ]
    
    for i in range(min(req.count, len(real_images))):
        images[i]["url"] = real_images[i] + f"&q={query.replace(' ', '+')}"
    
    return {"images": images, "query": query}

@app.get("/")
async def serve_index():
    index_path = Path(__file__).parent / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse("<h1>NeuraSite Generator - index.html not found</h1>")

@app.get("/generator")
async def serve_generator():
    gen_path = Path(__file__).parent / "generator.html"
    if gen_path.exists():
        return FileResponse(gen_path)
    index_path = Path(__file__).parent / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse("<h1>Generator not found</h1>")

# Статика для старых лендингов
@app.get("/old")
async def serve_old():
    old_path = Path(__file__).parent / "old-landing.html"
    if old_path.exists():
        return FileResponse(old_path)
    return HTMLResponse("<h1>Old landing not found</h1>")

if __name__ == "__main__":
    import uvicorn
    print(f"""
╔════════════════════════════════════════════════╗
║  NeuraSite AI - Генератор сайтов на Polza AI  ║
║  Port: {PORT}                                  ║
║  Polza Base: {POLZA_BASE_URL}                 ║
║  Polza Key: {'SET' if POLZA_API_KEY else 'NOT SET - укажите в UI'}          ║
╚════════════════════════════════════════════════╝

Открой: http://localhost:{PORT}
Docs: http://localhost:{PORT}/docs

Рекомендуемые модели Polza AI:
- Текст: anthropic/claude-sonnet-4-5 (лучший для фронта)
- Картинки: bytedance/seedream-4.5
- Видео: bytedance/seedance-2.5
    """)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
