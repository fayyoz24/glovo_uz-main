class MerchantType:
    FOOD = "food"
    GROCERY = "grocery"
    PHARMACY = "pharmacy"
    FLOWERS = "flowers"
    EXPRESS = "express"

    CHOICES = [
        (FOOD, "Food & Restaurant"),
        (GROCERY, "Grocery"),
        (PHARMACY, "Pharmacy"),
        (FLOWERS, "Flowers"),
        (EXPRESS, "Express Delivery"),
    ]


class MerchantStatus:
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REJECTED = "rejected"

    CHOICES = [
        (PENDING, "Pending Review"),
        (ACTIVE, "Active"),
        (SUSPENDED, "Suspended"),
        (REJECTED, "Rejected"),
    ]
