# Dasturxon — yangi kodni serverga deploy qilish

Har safar local mashinada (yoki frontend/backend repo'da) o'zgarish qilib, GitHub'ga push qilgandan keyin, serverni yangilash uchun shu ketma-ketlikni bajaring.

## 1. Serverga ulanish

```powershell
ssh -i "$env:USERPROFILE\Downloads\ssh-key-2026-07-27.key" ubuntu@130.61.137.94
```

## 2. Joriy holatni tekshirish

```bash
cd ~/glovo_uz-main
git status
```

Agar serverda qo'lda o'zgartirilgan fayl bo'lsa (masalan `settings.py`dagi CSRF tuzatishi), `git diff config/settings.py` bilan nima o'zgarganini ko'ring. Bu o'zgarish hali GitHub'dagi kodda yo'q bo'lsa, uni yo'qotib qo'ymaslik uchun eslab qoling.

## 3. Yangi kodni tortib olish

```bash
git pull origin main
```

(loyihangiz boshqa branch ishlatsa, `main` o'rniga o'sha nomni yozing)

Agar konflikt chiqsa:
```bash
git stash
git pull origin main
git stash pop
```

## 4. Backend'ni qayta build qilish

```bash
cd ~/glovo_uz-main/docker
docker compose --env-file ../.env.prod up -d --build
```

Bu `backend-api`, `celery-worker`, `celery-beat`, `channels-worker`, `telegram-bot` xizmatlarini yangi kod bilan qayta build qilib ishga tushiradi. **Yangi migratsiyalar avtomatik qo'llaniladi** — entrypoint skripti buni o'zi bajaradi, alohida buyruq kerak emas.

## 5. nginx'ni qayta ishga tushirish — HECH QACHON UNUTMANG

```bash
docker compose restart nginx
```

`backend-api` qayta yaratilgani uchun uning ichki IP manzili o'zgaradi. Agar nginx qayta ishga tushirilmasa, u eski IP'ga ulanishga urinib **502 Bad Gateway** qaytaradi — bu xato bir necha marta takrorlangan.

## 6. Holatni va migratsiya loglarini tekshirish

```bash
docker compose ps
docker compose logs --tail=40 backend-api
```

Barcha servislar `Up (healthy)` holatda bo'lishi, va loglarda migratsiyalar xatosiz o'tgani ko'rinishi kerak.

## 7. Health-check va real test

```bash
curl -s https://130.61.137.94.sslip.io/api/v1/health/
```

Kutilgan javob:
```json
{"status": "ok", "checks": {"database": "ok", "redis": "ok"}}
```

Shundan so'ng brauzerda yoki mobil ilovada yangi funksiyalarni real sinab ko'ring.

---

## Qisqa versiya (hammasi bitta joyda)

```bash
cd ~/glovo_uz-main
git status
git pull origin main
cd docker
docker compose --env-file ../.env.prod up -d --build
docker compose restart nginx
docker compose ps
curl -s https://130.61.137.94.sslip.io/api/v1/health/
```
