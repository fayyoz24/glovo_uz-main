class PromoError(Exception):
    """Base exception for promotions app."""

    def __init__(self, message: str, code: str = "promo_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class PromoNotFound(PromoError):
    def __init__(self, code: str = "promo_not_found"):
        super().__init__(message="Promo kod topilmadi.", code=code)


class PromoNotActive(PromoError):
    def __init__(self):
        super().__init__(message="Promo kod faol emas.", code="promo_not_active")


class PromoExpired(PromoError):
    def __init__(self):
        super().__init__(message="Promo kodning muddati tugagan.", code="promo_expired")


class PromoUsageLimitReached(PromoError):
    def __init__(self):
        super().__init__(message="Promo kod limiti tugagan.", code="promo_usage_limit_reached")


class PromoPerUserLimitReached(PromoError):
    def __init__(self):
        super().__init__(
            message="Siz bu promo kodni allaqachon ishlatgansiz.",
            code="promo_per_user_limit_reached",
        )


class PromoMinOrderNotMet(PromoError):
    def __init__(self, min_amount):
        super().__init__(
            message=f"Minimal buyurtma summasi: {min_amount} so'm.",
            code="promo_min_order_not_met",
        )


class PromoNotApplicableToMerchant(PromoError):
    def __init__(self):
        super().__init__(
            message="Bu promo kod ushbu do'kon uchun mos emas.",
            code="promo_not_applicable_to_merchant",
        )


class PromoNotApplicableToUser(PromoError):
    def __init__(self):
        super().__init__(
            message="Bu promo kod siz uchun mos emas.",
            code="promo_not_applicable_to_user",
        )
