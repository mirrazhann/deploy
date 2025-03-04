FROM python:3.11 as requirements-stage

WORKDIR /tmp

RUN pip install poetry==1.5.0

COPY ./pyproject.toml ./poetry.lock* /tmp/

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.11

WORKDIR /code

COPY --from=requirements-stage /tmp/requirements.txt .

RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

RUN pip install uvicorn

RUN pip install fastapi
RUN pip install sqlalchemy
RUN pip install pyjwt
RUN pip install attr
RUN pip install alembic
RUN pip install python-multipart

COPY . .

ENTRYPOINT [ "uvicorn", "app.main:app" ]