# promotions app

Glovo UZ platformasidagi promo kampaniyalar va referal tizimi.

## Fayl tuzilmasi

```
promotions/
├── __init__.py
├── apps.py
├── admin.py
├── urls.py              # Customer endpoints
├── admin_urls.py        # Admin endpoints
├── models/
│   ├── promo_campaign.py   – PromoCampaign
│   ├── promo_usage.py      – PromoUsage
│   └── referral.py         – ReferralCode, ReferralUsage
├── constants/
│   └── promo_constants.py  – DiscountType, PromoStatus, PromoTargetType
├── exceptions/          – PromoError va boshqalar
├── selectors/           – Faqat READ querylar
├── services/            – Biznes logika (PromoService, ReferralService)
├── permissions/         – IsAdminOrOps
├── tasks/               – Celery task'lar
├── migrations/
└── api/
    ├── serializers.py
    └── views.py
```

## config/urls.py ga qo'shish

```python
from django.urls import path, include

urlpatterns = [
    # ... boshqa applar ...

    # Customer endpoints
    path("api/v1/promotions/", include("promotions.urls")),

    # Admin endpoints
    path("api/v1/admin/promotions/", include("promotions.admin_urls")),
]
```

## config/settings.py ga qo'shish

```python
INSTALLED_APPS = [
    # ...
    "promotions.apps.PromotionsConfig",
    # ...
]
```

## Celery Beat sozlamalari (config/celery.py yoki settings.py)

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    # Har kuni yarim tunda muddati o'tganlarni belgilash
    "expire-stale-promos": {
        "task": "promotions.tasks.expire_stale_promos",
        "schedule": crontab(hour=0, minute=0),
    },
    # Har 5 daqiqada avtomatik faollashtirish
    "auto-activate-promos": {
        "task": "promotions.tasks.auto_activate_scheduled_promos",
        "schedule": crontab(minute="*/5"),
    },
}
```

## Boshqa applar bilan integratsiya

### carts app – promo kodni cart'ga qo'llash

```python
# apps/carts/services/cart_service.py
from promotions.exceptions import PromoError
from promotions.services import PromoService

class CartService:
    @staticmethod
    def apply_promo(cart, user, code: str):
        try:
            promo = PromoService.validate_promo(
                code=code,
                user=user,
                subtotal=cart.subtotal,
                merchant_id=cart.branch.merchant_id,
            )
        except PromoError as e:
            raise CartPromoError(e.message)

        discount_info = PromoService.calculate_discount(
            promo=promo,
            subtotal=cart.subtotal,
            delivery_fee=cart.delivery_fee,
        )
        cart.coupon = promo
        cart.discount_amount = discount_info["total_discount"]
        cart.save(update_fields=["coupon", "discount_amount", "updated_at"])
        return discount_info
```

### orders app – checkout paytida promo saqlash

```python
# apps/orders/services/order_service.py
from promotions.services import PromoService

class OrderService:
    @staticmethod
    @transaction.atomic
    def checkout(cart, user, ...):
        # ... order yaratish ...

        if cart.coupon:
            PromoService.apply_promo_to_order(
                promo=cart.coupon,
                user=user,
                order=order,
                discount_amount=cart.discount_amount,
            )

        return order
```

### accounts app – ro'yxatdan o'tishda referal

```python
# apps/accounts/services/auth_service.py
from promotions.services import ReferralService

class AuthService:
    @staticmethod
    def register(phone, otp, referral_code=None):
        user = User.objects.create(phone=phone, ...)

        if referral_code:
            ReferralService.apply_referral_on_registration(
                new_user=user,
                referral_code=referral_code,
            )

        return user
```

### orders app – birinchi buyurtmada referal bonus

```python
# orders/services/order_service.py
from promotions.services import ReferralService

# Buyurtma delivered holatiga o'tganda:
ReferralService.credit_referral_bonuses(referee_user=order.customer)
```

## API Endpoints

### Customer
| Method | URL | Tavsif |
|--------|-----|--------|
| POST | `/api/v1/promotions/validate/` | Promo kodni tekshirish |
| GET | `/api/v1/promotions/referral/` | O'z referal kodini ko'rish |

### Admin
| Method | URL | Tavsif |
|--------|-----|--------|
| GET | `/api/v1/admin/promotions/` | Kampaniyalar ro'yxati |
| POST | `/api/v1/admin/promotions/` | Yangi kampaniya yaratish |
| GET | `/api/v1/admin/promotions/{id}/` | Kampaniya detail |
| PATCH | `/api/v1/admin/promotions/{id}/` | Tahrirlash |
| POST | `/api/v1/admin/promotions/{id}/pause/` | To'xtatish |
| POST | `/api/v1/admin/promotions/{id}/activate/` | Faollashtirish |
| GET | `/api/v1/admin/promotions/{id}/usages/` | Foydalanish tarixi |
