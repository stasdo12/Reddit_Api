# Используйте официальный образ Python
FROM python:3.8-slim

# Установите необходимые зависимости
RUN pip install praw

# Копируйте скрипт и другие файлы в контейнер
COPY . /app

# Установите рабочую директорию
WORKDIR /app

# Установка кодировки UTF-8
ENV PYTHONIOENCODING=utf-8

# Запустите скрипт при запуске контейнера
CMD ["python", "final_Redit_api.py"]