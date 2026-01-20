FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание директории для данных (если volume не примонтирован)
RUN mkdir -p /data

# Переменная для БД
ENV DB_PATH=/data/monitor.db

# Запуск
CMD ["python", "main_loop.py"]
