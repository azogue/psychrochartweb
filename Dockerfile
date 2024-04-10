# ---- Base Node ----
FROM python:3.12-slim as base

# set working directory
WORKDIR /app
ENV PYTHONPATH /app

# Copy README & files needed for installation
COPY README.md .
COPY pyproject.toml .
COPY src/psychrochartweb psychrochartweb
RUN pip3 install "uv>=0.1.28" && uv pip -vv install --no-cache -r pyproject.toml --system -e .

# set envs
ENV HOST 0.0.0.0
ENV APP_PORT 8080
# expose port and define CMD
EXPOSE ${APP_PORT}
# Default command
CMD ["psychrocam"]
