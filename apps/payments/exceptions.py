class PaymentError(Exception):
    """Base payment exception."""
    pass


class PaymentProviderError(PaymentError):
    """Provider returned an error."""
    def __init__(self, message, code=None, raw=None):
        super().__init__(message)
        self.code = code
        self.raw = raw


class InvalidSignatureError(PaymentError):
    """Signature verification failed."""
    pass


class TransactionNotFound(PaymentError):
    pass


class TransactionAlreadyExists(PaymentError):
    pass


class OrderAlreadyPaid(PaymentError):
    pass


class RefundNotAllowed(PaymentError):
    pass
