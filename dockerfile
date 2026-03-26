FROM python:3.14-slim

WORKDIR /app

# Устанавливаем системные зависимости (иногда нужно)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаём папку для данных (чтобы не падало)
RUN mkdir -p user_data

EXPOSE 8080

# Более надёжный запуск Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--timeout", "120", \
     "--log-level", "info", \
     "app:app"]