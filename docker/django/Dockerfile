# =========================================================
# Glovo UZ Backend — Django/DRF Dockerfile
# Multi-stage build: builder (compiles deps) -> runtime (slim, no build tools)
# =========================================================

ARG PYTHON_VERSION=3.12-slim

# ---------- Stage 1: builder ----------
FROM python:${PYTHON_VERSION} AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# System deps needed only to build python wheels (psycopg2, Pillow, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libjpeg-dev \
    zlib1g-dev \
    libwebp-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Build dependency (env passed at build time: local | dev | staging | prod)
ARG REQUIREMENTS_FILE=requirements/prod.txt
COPY requirements/ requirements/
RUN pip wheel --wheel-dir /wheels -r ${REQUIREMENTS_FILE}

# ---------- Stage 2: runtime ----------
FROM python:${PYTHON_VERSION} AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    APP_HOME=/app

# Runtime system deps only (no compilers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libjpeg62-turbo \
    zlib1g \
    libwebp7 \
    netcat-openbsd \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r django && useradd -r -g django -d ${APP_HOME} -s /sbin/nologin django

WORKDIR ${APP_HOME}

# Install prebuilt wheels from the builder stage (fast, no compiling at runtime)
ARG REQUIREMENTS_FILE=requirements/prod.txt
COPY --from=builder /wheels /wheels
COPY requirements/ requirements/
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r ${REQUIREMENTS_FILE} \
    && rm -rf /wheels

# Copy project source
COPY . .

# Entrypoint / helper scripts
COPY docker/scripts/entrypoint.sh /entrypoint.sh
COPY docker/scripts/wait-for-it.sh /wait-for-it.sh
RUN chmod +x /entrypoint.sh /wait-for-it.sh

# Static & media roots (collectstatic target, mounted volume for media)
RUN mkdir -p ${APP_HOME}/staticfiles ${APP_HOME}/mediafiles \
    && chown -R django:django ${APP_HOME}

USER django

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "60"]
