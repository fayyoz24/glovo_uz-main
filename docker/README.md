# docker/

Dasturxon backendining konteynerizatsiya qatlami. Loyihaning qolgan qismi
(`config/`, `apps/`, `requirements.txt`, `manage.py`) allaqachon
mavjud bo'lib, quyidagi fayllar shularni import qilib ishlatadi.

## Tarkib

```
docker/
├── django/
│   ├── Dockerfile          # production image (multi-stage, gunicorn)
│   └── Dockerfile.dev      # local dev image (runserver, hot-reload)
├── nginx/
│   ├── nginx.conf
│   └── conf.d/
│       └── default.conf.template   # envsubst orqali render qilinadi
├── postgres/
│   └── init/
│       └── 01_extensions.sql       # uuid-ossp, pg_trgm, btree_gist, unaccent
├── scripts/
│   ├── entrypoint.sh        # migrate/collectstatic + SERVICE_ROLE dispatch
│   └── wait-for-it.sh       # postgres/redis tayyor bo'lishini kutish
├── docker-compose.yml       # prod/staging: barcha 7 servis (Section 26)
└── docker-compose.dev.yml   # local override (hot-reload, ochiq portlar)
```

## Servislar (Section 26 — Deployment Architecture)

| Servis            | Vazifasi                                              |
|--------------------|--------------------------------------------------------|
| `backend-api`       | Django/DRF, gunicorn (WSGI), REST API + webhooklar     |
| `channels-worker`   | Django Channels, daphne (ASGI), `/ws/*` realtime       |
| `celery-worker`     | Background job'lar (notifications, payments, dispatch) |
| `celery-beat`       | Periodik job'lar (reconciliation, auto-cancel va h.k.) |
| `postgres`          | PostgreSQL 16                                          |
| `redis`             | Celery broker/backend + Channels layer + cache         |
| `nginx`             | Reverse proxy, static/media, TLS, `/ws/` upgrade       |

## Ishga tushirish — Local development

```bash
cp .env.example .env
# .env ichida POSTGRES_*, REDIS_*, DJANGO_SECRET_KEY qiymatlarini to'ldiring

cd docker
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

API: `http://localhost:8000/`
Websocket: `ws://localhost:8001/ws/...`

## Ishga tushirish — Staging/Production

```bash
cp .env.example .env.prod
# real qiymatlar bilan to'ldiring (CLICK_*, PAYME_*, AWS_*, SENTRY_DSN va h.k.)

cd docker
docker compose --env-file ../.env.prod up -d --build
```

Nginx `${NGINX_SERVER_NAME}` ni `docker/nginx/conf.d/default.conf.template`
ichida `envsubst` orqali avtomatik almashtiradi (nginx rasmiy image'ining
`/etc/nginx/templates/` mexanizmi). TLS sertifikatlarni
`docker/nginx/certs/fullchain.pem` va `privkey.pem` ga joylashtiring.

## Muhim eslatmalar

- `SERVICE_ROLE` env o'zgaruvchisi `entrypoint.sh` ichida qaysi servis
  ekanini aniqlaydi (`api`, `worker`, `beat`, `channels`) — shunga qarab
  migration/collectstatic bosqichlari faqat `api` uchun ishlaydi.
- Yagona `requirements.txt` fayl ishlatiladi (build-time `REQUIREMENTS_FILE`
  argumenti shu faylga ishora qiladi — hozircha alohida local/prod fayllarga
  bo'linmagan).
- Postgres va Redis healthcheck'lari orqali boshqa servislar ular
  tayyor bo'lgandan keyin ishga tushadi (`depends_on: condition: service_healthy`).
- CI/CD (Section 27): GitHub Actions shu `docker/django/Dockerfile`ni
  build qilib, staging'ga avtomatik, production'ga manual approval bilan
  deploy qilishi mo'ljallangan.
