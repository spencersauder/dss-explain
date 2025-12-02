# DSSS Simulator Backend

Сервис на FastAPI, выполняющий численную симуляцию радиолинии с прямым расширением спектра (DSSS). Он предоставляет эндпоинты, которые использует фронтенд: назад возвращаются восстановленные сообщения, формы сигналов и спектры на каждом участке тракта.

## Быстрый старт

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn app.main:app --reload --port 8000
```

API будет доступен по адресу `http://localhost:8000/api`.

## Эндпоинты

### `POST /api/simulate`
Запуск полной цепочки: передача -> канал -> приём.

Тело запроса:

```json
{
  "message": "Hello, DSSS!",
  "tx_secret": "alpha",
  "rx_secret": "alpha",
  "chip_rate": 100000.0,
  "carrier_freq": 1000000.0,
  "noise_power": 0.25,
  "noise_bandwidth": 20000.0,
  "oversampling": 8,
  "coding_scheme": "hamming74"
}
```

Ответ:

```json
{
  "simulation_id": "...",
  "decoded_message": "Hello, DSSS!",
  "mismatch": false,
  "coding_scheme": "hamming74",
  "noise_bandwidth": 20000.0,
  "available_stages": ["source", "spreader", "modulator", "channel", "correlator", "decoder"],
  "inline_spectra": [
    {
      "stage": "modulator",
      "frequencies": [...],
      "magnitudes": [...],
      "sample_rate": 800000.0
    }
  ]
}
```

### `GET /api/spectra/{stage}`
Получение формы сигнала и спектра для выбранного участка ранее выполненной симуляции.

Параметры запроса:

- `simulation_id` — идентификатор, возвращённый `/api/simulate`

Ответ:

```json
{
  "stage": "channel",
  "waveform": { "samples": [...], "sample_rate": 800000.0 },
  "spectrum": { "frequencies": [...], "magnitudes": [...], "sample_rate": 800000.0 }
}
```

## Тесты

```bash
cd backend
source .venv/bin/activate
pytest
```

Набор покрывает численный движок и публичный API.
