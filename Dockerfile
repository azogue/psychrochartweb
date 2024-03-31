# ---- Base Node ----
FROM python:3.12-slim as base

RUN apt-get update \
    && apt-get install --no-install-recommends -y locales build-essential curl libatlas3-base liblapack3 libfreetype6-dev \
    && curl -sSL https://install.python-poetry.org/ | POETRY_HOME=/opt/poetry python \
    && cd /usr/local/bin \
    && ln -s /opt/poetry/bin/poetry \
    && poetry config virtualenvs.create false \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# set working directory
WORKDIR /app
ENV PYTHONPATH /app

# Setup locales
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Copy README & files needed for installation
COPY README.md .
COPY pyproject.toml .
COPY poetry.lock .
COPY psychrochartweb psychrochartweb
RUN poetry install --only main

# set envs
ENV HOST 0.0.0.0
ENV APP_PORT 8080
# expose port and define CMD
EXPOSE ${APP_PORT}
# Default command
CMD ["python", "-m", "psychrochartweb"]
