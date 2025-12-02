# DSSS Link Visualizer

Интерактивный стенд, иллюстрирующий работу модуляции Direct Sequence Spread Spectrum (DSSS). Проект включает FastAPI-бэкенд с численной симуляцией и фронтенд на React/TypeScript, который визуализирует цепочку передачи/приёма, спектры и восстановленные сообщения.

## Архитектура

- `backend/`: сервис симуляции на FastAPI + NumPy (`python3 -m venv .venv && pip install -e .[dev]`).
- `frontend/`: клиент на Vite + React (`npm install && npm run dev`).

UI общается с бэкендом по эндпоинтам `/api/*` и может запускаться отдельно в режиме разработки. Vite проксирует `/api` на `http://localhost:8000` при выполнении `npm run dev`.

## Локальная разработка

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev -- --host
```

Интерфейс доступен по адресу http://localhost:5173.

### Тесты
```bash
cd backend
source .venv/bin/activate
pytest
```
```bash
cd frontend
npm run build   # проверка типов и сборка через Vite
```

## Возможности

- Ввод сообщения и раздельных секретных фраз для передатчика/приёмника.
- Настройка скорости чипов, несущей и коэффициента передискретизации.
- Управление мощностью шума канала для наблюдения изменений спектра.
- Просмотр спектров и форм сигналов на каждом этапе DSSS-тракта.
- Индикация, совпадает ли принятое сообщение с отправленным.
