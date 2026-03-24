# Используем официальный образ Python 3.14
# VSCode может показывать предупреждение, но образ существует
FROM python:3.14-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Открываем порт (Back4app обычно использует 8080)
EXPOSE 8080

# Команда запуска (Flask + бот в фоне)
CMD ["sh", "-c", "gunicorn -w 4 -b 0.0.0.0:8080 app:app"]