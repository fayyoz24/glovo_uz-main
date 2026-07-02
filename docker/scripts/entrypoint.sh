#!/usr/bin/env bash
# =========================================================
# Entrypoint for all Django-based containers:
#   backend-api, celery-worker, celery-beat, channels/websocket
#
# Behavior is controlled by the SERVICE_ROLE env var so this single
# script can be reused across every service defined in docker-compose.
# =========================================================
set -e

DB_HOST="${POSTGRES_HOST:-postgres}"
DB_PORT="${POSTGRES_PORT:-5432}"
REDIS_HOST_VALUE="${REDIS_HOST:-redis}"
REDIS_PORT_VALUE="${REDIS_PORT:-6379}"
SERVICE_ROLE="${SERVICE_ROLE:-api}"

echo ">>> [entrypoint] starting service role: ${SERVICE_ROLE}"

# ---- Wait for Postgres ----
echo ">>> [entrypoint] waiting for postgres at ${DB_HOST}:${DB_PORT}..."
/wait-for-it.sh "${DB_HOST}:${DB_PORT}" --timeout=60 --strict -- echo ">>> [entrypoint] postgres is up"

# ---- Wait for Redis ----
echo ">>> [entrypoint] waiting for redis at ${REDIS_HOST_VALUE}:${REDIS_PORT_VALUE}..."
/wait-for-it.sh "${REDIS_HOST_VALUE}:${REDIS_PORT_VALUE}" --timeout=60 --strict -- echo ">>> [entrypoint] redis is up"

run_migrations() {
    echo ">>> [entrypoint] running migrations..."
    python manage.py migrate --noinput
}

collect_static() {
    if [ "${DJANGO_SETTINGS_MODULE}" != "config.settings.local" ]; then
        echo ">>> [entrypoint] collecting static files..."
        python manage.py collectstatic --noinput --clear
    fi
}

case "${SERVICE_ROLE}" in
  api)
    run_migrations
    collect_static
    ;;
  worker)
    # Migrations are owned by the api service; worker just waits for deps.
    echo ">>> [entrypoint] celery worker ready, skipping migrate/collectstatic"
    ;;
  beat)
    echo ">>> [entrypoint] celery beat ready, skipping migrate/collectstatic"
    ;;
  channels)
    echo ">>> [entrypoint] channels/websocket worker ready, skipping migrate/collectstatic"
    ;;
  *)
    echo ">>> [entrypoint] unknown SERVICE_ROLE='${SERVICE_ROLE}', running default boot steps"
    run_migrations
    ;;
esac

echo ">>> [entrypoint] handing off to: $*"
exec "$@"
