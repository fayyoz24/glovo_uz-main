# Dasturxon — Oracle Cloud Free Tier'ga deploy qilish

Bu qo'llanma sizning mavjud `docker/docker-compose.yml` setupingizni (backend-api,
channels-worker, celery-worker, celery-beat, telegram-bot, postgres, redis, nginx)
Oracle Cloud'ning **doim bepul (Always Free)** VM'iga qanday joylashtirishni
bosqichma-bosqich tushuntiradi.

Davom etishdan oldin, kodga kiritilgan tuzatishlar:
- `config/settings.py` — Channels Redis ulanishiga parol qo'shildi (`REDIS_PASSWORD` endi ishlatiladi)
- `.env.example` — Celery URL'lari `redis:6379` + parol bilan to'g'irlandi, tasodifiy qolib ketgan matn va **oshkor bo'lgan haqiqiy bot tokeni** olib tashlandi
- `apps/common/api/health.py` + `apps/common/urls.py` — `/api/v1/health/` endpointi qo'shildi (nginx va docker-compose shunga tayanadi, lekin u mavjud emas edi)
- `docker/scripts/entrypoint.sh` — `telegram_bot` roli uchun alohida holat qo'shildi (avval `backend-api` bilan bir vaqtda migratsiyani qayta ishga tushirishga urinardi)
- `docker/docker-compose.yml` — `certbot` servisi va `certbot_webroot` volume qo'shildi (Let's Encrypt sertifikatini avtomatik olish uchun)

## ⚠️ Birinchi qadam — bot tokenini bekor qiling

`.env.example` faylida haqiqiy Telegram bot tokeni ochiq holda saqlangan edi.
Deploy qilishdan oldin:
1. Telegram'da **@BotFather** ga o'ting
2. `/mybots` → botingizni tanlang → **API Token** → **Revoke current token**
3. Yangi tokenni faqat serverdagi `.env` fayliga yozing (hech qachon git'ga commit qilmang)

---

## 1-qadam — Oracle Cloud hisobini ochish va VM yaratish

1. https://www.oracle.com/cloud/free/ orqali ro'yxatdan o'ting (karta talab qilinadi, lekin Always Free resurslar uchun pul yechilmaydi)
2. Console → **Compute** → **Instances** → **Create Instance**
3. Sozlamalar:
   - **Image**: Ubuntu 24.04 (Always Free eligible)
   - **Shape**: `VM.Standard.A1.Flex` (Ampere/ARM) → 2 OCPU / 12 GB RAM tanlang (Always Free limitiga mos)
   - **SSH keys**: o'zingizning public key'ingizni yuklang (yoki Oracle generatsiya qilgan keyni yuklab oling)
4. **Create** tugmasini bosing, VM ishga tushishini kuting (~2 daqiqa)
5. Instance sahifasida **Public IP** manzilini yozib oling

### Portlarni ochish (juda muhim — Oracle'da 2 marta ochish kerak)

**a) Security List / Network Security Group (Console'da):**
- Instance → **Subnet** → **Security Lists** → **Default Security List**
- **Add Ingress Rules**: `0.0.0.0/0` dan TCP `80`, TCP `443` uchun ruxsat qo'shing

**b) VM ichidagi firewall (iptables/ufw):**
```bash
ssh ubuntu@<PUBLIC_IP>

sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```
(Ikkalasini ham ochmasangiz, sayt tashqaridan ochilmaydi — bu Oracle'ga xos eng ko'p uchraydigan xato.)

---

## 2-qadam — Docker o'rnatish

```bash
ssh ubuntu@<PUBLIC_IP>

curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
newgrp docker

# tekshirish
docker --version
docker compose version
```

---

## 3-qadam — Domenni yo'naltirish

Domen provayderingizda (masalan Namecheap, Cloudflare) **A record** qo'shing:
```
api.sizningdomeningiz.uz  →  <PUBLIC_IP>
```
DNS tarqalishini kuting (odatda 5-30 daqiqa): `ping api.sizningdomeningiz.uz`

---

## 4-qadam — Loyihani serverga yuklash

```bash
git clone <sizning-repo-url> ~/dasturxon
cd ~/dasturxon

cp .env.example .env.prod
nano .env.prod
```

`.env.prod` faylida albatta o'zgartiring:
```
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<python -c "import secrets; print(secrets.token_urlsafe(50))" natijasi>
DJANGO_ALLOWED_HOSTS=api.sizningdomeningiz.uz
DJANGO_CSRF_TRUSTED_ORIGINS=https://api.sizningdomeningiz.uz

POSTGRES_PASSWORD=<kuchli-parol>
REDIS_PASSWORD=<kuchli-parol>

# Redis/Celery — parolni yuqoridagi REDIS_PASSWORD bilan bir xil qiling
REDIS_URL=redis://:<kuchli-parol>@redis:6379/0
CELERY_BROKER_URL=redis://:<kuchli-parol>@redis:6379/1
CELERY_RESULT_BACKEND=redis://:<kuchli-parol>@redis:6379/2

NGINX_SERVER_NAME=api.sizningdomeningiz.uz

TELEGRAM_BOT_TOKEN=<BotFather'dan olingan YANGI token>
TELEGRAM_BOT_SHARED_SECRET=<tasodifiy uzun satr>
TELEGRAM_WEBHOOK_SECRET=<tasodifiy uzun satr>
BACKEND_BASE_URL=https://api.sizningdomeningiz.uz

CORS_ALLOWED_ORIGINS=https://sizningdomeningiz.uz
```

---

## 5-qadam — TLS sertifikat olish (Let's Encrypt, bepul)

Nginx SSL konfiguratsiyasi sertifikat fayllarini kutadi, lekin ular hali yo'q —
shuning uchun avval **vaqtincha HTTP-only** rejimda ishga tushiramiz, sertifikat
olamiz, keyin to'liq HTTPS'ga o'tamiz.

```bash
cd ~/dasturxon/docker

# 5.1 — vaqtincha faqat backend-api + nginx'ni HTTP rejimida ko'taramiz
#       (default.conf.template'dagi "return 301 https://..." qatorini vaqtincha izohga oling)
sed -i 's/return 301 https:\/\/\$host\$request_uri;/# &/' nginx/conf.d/default.conf.template

docker compose --env-file ../.env.prod up -d postgres redis backend-api channels-worker nginx

# 5.2 — sertifikat so'rash (webroot usuli, nginx allaqachon /.well-known/... ni ochib qo'ygan)
docker compose --env-file ../.env.prod run --rm certbot \
  certbot certonly --webroot -w /var/www/certbot \
  -d api.sizningdomeningiz.uz \
  --email sizning@email.uz --agree-tos --no-eff-email

# 5.3 — certbot sertifikatlarni /etc/letsencrypt/live/... ga yozadi, nginx esa
#       /etc/nginx/certs/fullchain.pem va privkey.pem kutadi — symlink qilamiz
sudo ln -sf nginx/certs/live/api.sizningdomeningiz.uz/fullchain.pem nginx/certs/fullchain.pem
sudo ln -sf nginx/certs/live/api.sizningdomeningiz.uz/privkey.pem nginx/certs/privkey.pem

# 5.4 — HTTP→HTTPS redirect qatorini qaytaramiz va nginx'ni qayta ishga tushiramiz
sed -i 's/# return 301 https:\/\/\$host\$request_uri;/return 301 https:\/\/$host$request_uri;/' nginx/conf.d/default.conf.template
docker compose --env-file ../.env.prod restart nginx
```

Tekshirish: `https://api.sizningdomeningiz.uz/api/v1/health/` — `{"status": "ok", ...}` qaytishi kerak.

### Avtomatik yangilash (sertifikat 90 kunda tugaydi)

```bash
crontab -e
```
Quyidagi qatorni qo'shing (har hafta yakshanba, soat 03:00 da tekshiradi):
```
0 3 * * 0 cd ~/dasturxon/docker && docker compose --env-file ../.env.prod run --rm certbot renew --webroot -w /var/www/certbot && docker compose --env-file ../.env.prod restart nginx
```

---

## 6-qadam — Butun stackni ishga tushirish

```bash
cd ~/dasturxon/docker
docker compose --env-file ../.env.prod up -d --build
```

Bu 7 ta konteynerni ko'taradi: `postgres`, `redis`, `backend-api`, `channels-worker`,
`celery-worker`, `celery-beat`, `telegram-bot`, `nginx`.

### Holat va loglarni tekshirish

```bash
docker compose --env-file ../.env.prod ps
docker compose --env-file ../.env.prod logs -f backend-api
docker compose --env-file ../.env.prod logs -f telegram-bot
docker compose --env-file ../.env.prod logs -f celery-worker
```

### Admin foydalanuvchi yaratish

```bash
docker compose --env-file ../.env.prod exec backend-api python manage.py createsuperuser
```

---

## 7-qadam — Frontend (React) deploy qilish

Backend VM'da, lekin frontend uchun bepul static hosting (Vercel/Cloudflare Pages)
ancha qulay — build va CDN avtomatik, spin-down muammosi yo'q (chunki static fayl).

**Vercel bilan:**
```bash
cd glovo-frontend-main
npm install -g vercel
vercel
```
Deploy paytida environment variable qo'shing:
```
VITE_API_BASE_URL=https://api.sizningdomeningiz.uz/api/v1
```

Frontend WebSocket ulanishi (`orderSocket.js`, `courierSocket.js`) `API_BASE_URL`dan
avtomatik `wss://api.sizningdomeningiz.uz/ws/...` manzilini quradi — qo'shimcha sozlash shart emas.

---

## 8-qadam — Xavfsizlik va monitoring (tavsiya)

- **Backup**: `docker compose exec postgres pg_dump -U dasturxon_user dasturxon > backup.sql` — cron orqali kunlik
- **Sentry** (`.env.prod`dagi `SENTRY_DSN`) — xatolarni kuzatish uchun bepul tarif yetarli
- **UFW**: `sudo ufw allow 22,80,443/tcp && sudo ufw enable` (SSH portini unutmang!)
- **Oracle "idle reclamation"**: real trafik (bot, celery) doim ishlab turgani sabab bu odatda muammo bo'lmaydi, lekin CPU deyarli 0% bo'lsa VM cheklanishi mumkin

---

## Tezkor buyruqlar (kelajakda foydalanish uchun)

```bash
# Yangilash (git pull + qayta build)
cd ~/dasturxon && git pull
cd docker && docker compose --env-file ../.env.prod up -d --build

# Bitta servisni qayta ishga tushirish
docker compose --env-file ../.env.prod restart celery-worker

# Migratsiya qo'lda
docker compose --env-file ../.env.prod exec backend-api python manage.py migrate

# Hamma narsani to'xtatish (ma'lumotlar saqlanadi)
docker compose --env-file ../.env.prod down

# Hamma narsani o'chirish (ma'lumotlar HAM o'chadi — ehtiyot bo'ling)
docker compose --env-file ../.env.prod down -v
```
