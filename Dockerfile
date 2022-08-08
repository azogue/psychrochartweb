# ---- Base Node ----
FROM python:3.9-slim-buster as base

RUN apt update -qq \
    && apt upgrade -y \
    && apt install -y \
        curl gcc git locales locales-all make nano openssh-client \
        libatlas3-base liblapack3 libfreetype6-dev \
        python3-dev pkg-config \
    && apt autoremove -y

RUN pip3 install virtualenv

RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | POETRY_HOME=/opt/poetry python \
    && cd /usr/local/bin \
    && ln -s /opt/poetry/bin/poetry \
    && poetry config virtualenvs.create false

# set working directory
WORKDIR /app

# ---- Dependencies ----
FROM base AS deps

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

RUN poetry install --no-dev

# ---- Development dependencies ----
FROM deps AS dev-deps

# set envs
ENV HOST 0.0.0.0
ENV PORT 80
# expose port and define CMD
EXPOSE ${PORT}
# Default command
CMD ["poetry", "run", "python", "-m", "psychrochartweb"]
