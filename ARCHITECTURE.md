# Архитектура сервиса

## Компоненты

### 1. The Watcher (Go Service)
Сервис, работающий в фоне.
*   **Discovery Module:** Раз в 10 минут запрашивает `/models` у OpenRouter. Обновляет таблицу `models`.
*   **Poller Module:** Раз в 5 минут (конфигурируемо) запускает проверку активных моделей.
    *   Использует Goroutines для параллельного опроса (чтобы не ждать по очереди).
    *   Отправляет результаты в БД.

### 2. Database (SQLite)
Файл `monitor.db`.

**Таблица `models`:**
*   `id` (string, openrouter id)
*   `name` (string)
*   `is_free` (bool)
*   `last_seen` (timestamp) - чтобы детектировать удаление.
*   `is_active` (bool)

**Таблица `checks`:**
*   `id` (int)
*   `model_id` (fk)
*   `timestamp` (datetime)
*   `status_code` (int)
*   `latency_ms` (int)
*   `success` (bool) - прошел ли тест на адекватность.
*   `error_msg` (text)

### 3. Web Server (Go + Templates или API)
Простой HTTP сервер, встроенный в тот же бинарник.
*   `GET /`: HTML страница со статусом.
*   `GET /api/status`: JSON для внешних интеграций.

## Алгоритм проверки (Probe)

1.  **Request:**
    ```json
    {
      "model": "model_id",
      "messages": [{"role": "user", "content": "Test."}],
      "max_tokens": 5
    }
    ```
2.  **Validation:**
    *   HTTP 200? -> OK.
    *   HTTP 429/5xx -> FAIL.
    *   Response timeout (e.g. 10s) -> FAIL.
