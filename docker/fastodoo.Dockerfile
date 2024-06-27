FROM python:3.11-bullseye

# install poetry
RUN pip install poetry

# install dependencies
COPY pyproject.toml poetry.lock /app/
WORKDIR /app
# RUN poetry install --no-root
RUN poetry config virtualenvs.create false \
  && poetry install --no-interaction --no-ansi

# copy code
COPY . /app

CMD ["fastapi", "run", "main.py", "--port", "80"]