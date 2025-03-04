# Этап формирования файла requirements.txt с помощью poetry
FROM python:3.11 as requirements-stage

WORKDIR /tmp

# Устанавливаем poetry
RUN pip install poetry==1.5.0

# Копируем файлы с зависимостями (обратите внимание на пробелы между аргументами)
COPY ./pyproject.toml ./poetry.lock* /tmp/

# Экспорт зависимостей в requirements.txt.
# Обратите внимание: используются двойные дефисы для параметров
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Финальный этап: создание образа приложения
FROM python:3.11

WORKDIR /code

# Копируем файл requirements.txt из предыдущего этапа
COPY --from=requirements-stage /tmp/requirements.txt .

# Устанавливаем зависимости с нужными флагами (с двойными дефисами)
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

# Копируем исходный код приложения (замените '.' на нужную директорию, если требуется)
COPY . .

ENTRYPOINT [ "uvicorn", "app.main:app" ]