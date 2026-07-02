class ProductStatus:
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"

    CHOICES = [
        (ACTIVE, "Active"),
        (INACTIVE, "Inactive"),
        (OUT_OF_STOCK, "Out of Stock"),
    ]


class ModifierGroupType:
    SINGLE = "single"    # radio — faqat 1 ta tanlash
    MULTI = "multi"      # checkbox — bir nechta tanlash

    CHOICES = [
        (SINGLE, "Single Choice"),
        (MULTI, "Multiple Choice"),
    ]
