class ReviewError(Exception):
    def __init__(self, message: str, code: str = "review_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class ReviewNotFound(ReviewError):
    def __init__(self):
        super().__init__("Review topilmadi.", "review_not_found")


class ReviewAlreadyExists(ReviewError):
    def __init__(self):
        super().__init__(
            "Siz bu buyurtmaga allaqachon review qoldirgansiz.",
            "review_already_exists",
        )


class ReviewNotAllowed(ReviewError):
    def __init__(self):
        super().__init__(
            "Faqat yetkazilgan buyurtmalarni baholash mumkin.",
            "review_not_allowed",
        )


class ReviewNotOwner(ReviewError):
    def __init__(self):
        super().__init__(
            "Bu review sizga tegishli emas.",
            "review_not_owner",
        )


class ReviewAlreadyReplied(ReviewError):
    def __init__(self):
        super().__init__(
            "Bu reviewga allaqachon javob berilgan.",
            "review_already_replied",
        )
