# reviews app

Glovo UZ platformasidagi mijoz reytinglari va sharhlar tizimi.

## Fayl tuzilmasi

```
reviews/
├── __init__.py
├── apps.py
├── admin.py
├── urls.py              # Customer + public endpoints
├── merchant_urls.py     # Merchant panel endpoints
├── admin_urls.py        # Admin endpoints
├── models/
│   ├── review.py        – Review (asosiy model)
│   ├── review_image.py  – ReviewImage (rasm)
│   └── review_flag.py   – ReviewFlag (shikoyat)
├── constants/           – ReviewType, ReviewStatus, RATING_CHOICES
├── exceptions/          – ReviewError va 5 ta typed exception
├── selectors/           – Faqat READ querylar
├── services/            – ReviewService (biznes logika)
├── permissions/         – IsAdminOrOps, IsMerchantStaff, IsReviewOwner
├── tasks/               – Celery task'lar
├── migrations/
└── api/
    ├── serializers.py
    └── views.py
```

## config/urls.py ga qo'shish

```python
urlpatterns = [
    # Customer + public
    path("api/v1/", include("reviews.urls")),

    # Merchant panel
    path("api/v1/merchant/", include("reviews.merchant_urls")),

    # Admin
    path("api/v1/admin/", include("reviews.admin_urls")),
]
```

## config/settings.py

```python
INSTALLED_APPS = [
    # ...
    "reviews.apps.ReviewsConfig",
]
```

## Celery Beat (settings.py)

```python
CELERY_BEAT_SCHEDULE = {
    "recalculate-merchant-ratings": {
        "task": "reviews.tasks.recalculate_merchant_ratings",
        "schedule": crontab(hour=3, minute=0),  # har kuni soat 03:00
    },
    "recalculate-courier-ratings": {
        "task": "reviews.tasks.recalculate_courier_ratings",
        "schedule": crontab(hour=3, minute=30),
    },
}
```

## Boshqa applar bilan integratsiya

### orders app – delivered bo'lganda review yozdirish

Review yozish order'ning `delivered` statusidan keyin mumkin.
Orders serializer'iga `has_review` maydoni qo'shish:

```python
# orders/api/serializers.py
from reviews.selectors import get_review_by_order

class OrderDetailSerializer(serializers.ModelSerializer):
    has_review = serializers.SerializerMethodField()

    def get_has_review(self, obj) -> bool:
        return get_review_by_order(obj.id) is not None
```

### notifications app – yangi review bildirishnomasi

Review yaratilgandan keyin task chaqirish:

```python
# reviews/services/__init__.py – create_review ichida:
from reviews.tasks import notify_merchant_new_review
notify_merchant_new_review.delay(str(review.id))
```

### merchants app – rating_avg maydoni

`Merchant` modelida `rating_avg` maydoni bo'lishi kerak:

```python
# merchants/models/merchant.py
rating_avg = models.DecimalField(max_digits=3, decimal_places=2, default=0)
```

### accounts app – CourierProfile.rating

```python
# accounts/models/courier_profile.py
rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
```

## API Endpoints

### Customer
| Method | URL | Tavsif |
|--------|-----|--------|
| POST | `/api/v1/orders/{order_id}/review/` | Review yozish |
| GET | `/api/v1/reviews/my/` | O'z reviewlarim |
| GET | `/api/v1/reviews/{id}/` | Review detail |
| PATCH | `/api/v1/reviews/{id}/` | Tahrirlash (24 soat) |
| POST | `/api/v1/reviews/{id}/flag/` | Shikoyat |

### Public (auth shart emas)
| Method | URL | Tavsif |
|--------|-----|--------|
| GET | `/api/v1/merchants/{id}/reviews/` | Do'kon reviewlari |
| GET | `/api/v1/merchants/{id}/rating-stats/` | Reyting statistikasi |

### Merchant panel
| Method | URL | Tavsif |
|--------|-----|--------|
| GET | `/api/v1/merchant/reviews/` | O'z do'koniga kelgan reviewlar |
| POST | `/api/v1/merchant/reviews/{id}/reply/` | Reviewga javob |

### Admin
| Method | URL | Tavsif |
|--------|-----|--------|
| GET | `/api/v1/admin/reviews/` | Barcha reviewlar (filter) |
| GET | `/api/v1/admin/reviews/{id}/` | Detail |
| POST | `/api/v1/admin/reviews/{id}/hide/` | Yashirish |
| POST | `/api/v1/admin/reviews/{id}/restore/` | Tiklash |

## Biznes qoidalar

- Faqat `delivered` buyurtma baholanadi
- Har bir buyurtma uchun **bitta** review (OneToOne)
- Mijoz reviewni **24 soat ichida** tahrirlay oladi
- 3+ shikoyat → review avtomatik `FLAGGED` holatiga o'tadi
- Merchant faqat **bir marta** javob bera oladi
- Review yashirilsa/tiklanganida merchant va kuryer reytingi avtomatik yangilanadi
- Do'kon sahifasida mijoz ismi `A***` ko'rinishida ko'rsatiladi (maxfiylik)
