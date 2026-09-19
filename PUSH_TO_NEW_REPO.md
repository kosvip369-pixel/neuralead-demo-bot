# Как залить генератор в новый репозиторий Neyrogenerator

Ты создал новый репозиторий https://github.com/kosvip369-pixel/Neyrogenerator — он пустой.
Arena-бот не имеет прав пушить в новые репо (только в arena ветку старого neuralead-demo-bot), поэтому нужно залить вручную — 2 минуты.

## Вариант 1: Через веб-интерфейс GitHub (самый простой)

1. Иди на https://github.com/kosvip369-pixel/Neyrogenerator
2. Нажми **Add file → Upload files**
3. Открой папку `/home/user/neurasite-ai-generator/` (или скачай zip `neurasite-ai-generator.zip` и распакуй)
4. Перетащи ВСЕ файлы из папки в окно GitHub (включая скрытые `.github`):
   - index.html
   - generator.html
   - generator_server.py
   - app.py
   - polza_models.json
   - templates.json
   - KEYS.md
   - TUTORIAL.md
   - README.md
   - requirements.txt
   - .env.example
   - .gitignore
   - Dockerfile
   - папка .github/workflows/pages.yml
   - папка examples/README.md
5. Внизу напиши коммит: `feat: NeuraSite AI Generator v2.0`
6. Нажми **Commit changes**

## Вариант 2: Через git локально (если есть git)

```bash
# Скачай архив или клонируй старый репо
git clone https://github.com/kosvip369-pixel/Neyrogenerator.git
cd Neyrogenerator

# Скопируй файлы из подготовленной папки
cp -r /home/user/neurasite-ai-generator/* .
cp -r /home/user/neurasite-ai-generator/.github .
cp /home/user/neurasite-ai-generator/.gitignore .

# Закоммить и запушь
git add -A
git commit -m "feat: NeuraSite AI Generator v2.0"
git push origin main
```

## Вариант 3: Я уже подготовил всё в arena ветке старого репо

В старом репо `neuralead-demo-bot` ветка `arena/01a0baf5-neuralead-demo-bot` уже содержит:
- `generator.html` — генератор (работает)
- `index.html` — теперь хаб: старый лендинг + баннер на генератор
- Все файлы генератора

Можешь просто скопировать оттуда.

## После заливки — включи GitHub Pages

1. В новом репо Neyrogenerator иди в **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: **main** / **root**
4. Save
5. Через 1-2 минуты сайт будет на https://kosvip369-pixel.github.io/Neyrogenerator/

Готово! Генератор работает.

## Проверка

После деплоя открой https://kosvip369-pixel.github.io/Neyrogenerator/ — должен открыться генератор.
Вставь Polza API ключ в шапке (поле 🔑) и генерируй.

Если не работает — смотри KEYS.md
