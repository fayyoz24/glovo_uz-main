"""
Payme Business (payme.uz) payment provider integration.

Payme uses JSON-RPC 2.0 over HTTP.
All requests come to a single endpoint; method name identifies the action.

Methods:
  CheckPerformTransaction  — verify order can be paid
  CreateTransaction        — create/retrieve transaction
  PerformTransaction       — mark as paid
  CancelTransaction        — cancel/refund
  CheckTransaction         — get transaction status
  GetStatement             — reconciliation (admin)

Docs: https://developer.paycom.uz/
"""

import base64
import hashlib
import logging
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from apps.payments.exceptions import PaymentError
from apps.payments.models import PaymentStatus, PaymentTransaction

logger = logging.getLogger(__name__)

# Payme error codes
PAYME_ERRORS = {
    -32300: "Cannot perform this operation",
    -32400: "System error",
    -32504: "Insufficient funds",
    -32600: "Invalid RPC request",
    -32601: "Method not found",
    -32602: "Invalid or missing parameter",
    -32603: "Internal server error",
    -31001: "Order not found",
    -31003: "Cannot cancel transaction",
    -31008: "Permission denied",
    -31050: "Order does not exist",
    -31051: "Order not ready for payment",
    -31052: "Order amount mismatch",
    -31060: "Transaction not found",
    -31061: "Transaction already exists",
    -31062: "Transaction already cancelled",
    -31064: "Refund amount exceeded",
    -31099: "Unknown error",
}

# Payme transaction states
STATE_CREATED = 1
STATE_COMPLETED = 2
STATE_CANCELLED = -1
STATE_CANCELLED_AFTER_COMPLETE = -2

# Cancel reasons
REASON_RECEIVERS_NOT_FOUND = 1
REASON_PROCESSING_EXECUTION_FAILED = 2
REASON_EXECUTION_FAILED = 3
REASON_CANCELLED_BY_TIMEOUT = 4
REASON_FUND_RETURNED = 5
REASON_UNKNOWN = 10


def _get_settings():
    return {
        "merchant_id": settings.PAYME_MERCHANT_ID,
        "secret_key": settings.PAYME_SECRET_KEY,  # cashier key (from Payme cabinet)
        "test_key": getattr(settings, "PAYME_TEST_KEY", None),
        "is_test": getattr(settings, "PAYME_TEST_MODE", False),
    }


def build_payment_url(transaction: PaymentTransaction) -> str:
    """
    Returns Payme checkout URL (payme.uz redirect link).
    The payload is base64-encoded JSON.
    """
    cfg = _get_settings()
    merchant_id = cfg["merchant_id"]

    amount_tiyin = transaction.amount_tiyin  # Payme uses tiyin

    # Payme expects: m=merchant_id;ac.order_id=xxx;a=amount_tiyin;c=callback_url
    raw = (
        f"m={merchant_id};"
        f"ac.order_id={transaction.order_id};"
        f"a={amount_tiyin};"
        f"c={settings.PAYME_RETURN_URL}"
    )
    encoded = base64.b64encode(raw.encode()).decode()

    base_url = "https://checkout.paycom.uz" if not cfg["is_test"] else "https://test.paycom.uz"
    return f"{base_url}/{encoded}"


def verify_auth(request) -> bool:
    """
    Payme authenticates via HTTP Basic Auth.
    Username: Paycom (always)
    Password: secret_key (or test_key in test mode)
    """
    cfg = _get_settings()
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Basic "):
        return False

    try:
        decoded = base64.b64decode(auth_header[6:]).decode()
        username, password = decoded.split(":", 1)
    except Exception:
        return False

    expected_key = cfg["test_key"] if cfg["is_test"] else cfg["secret_key"]
    return username == "Paycom" and password == expected_key


def _ok(request_id, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _error(request_id, code: int, message: str = None, data: str = None) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": code,
            "message": message or PAYME_ERRORS.get(code, "Error"),
            "data": data,
        },
    }


# ------------------------------------------------------------------
# Method handlers
# ------------------------------------------------------------------

def check_perform_transaction(params: dict, request_id) -> dict:
    """Verify that order can be paid before creating transaction."""
    account = params.get("account", {})
    order_id = account.get("order_id")
    amount = params.get("amount")  # tiyin

    try:
        from apps.orders.models import Order  # avoid circular import
        order = Order.objects.get(id=order_id)
    except Exception:
        return _error(request_id, -31050, data="order_id")

    if order.payment_status == "paid":
        return _error(request_id, -31061)

    # Validate amount
    expected_tiyin = int(order.total_amount * 100)
    if int(amount) != expected_tiyin:
        return _error(request_id, -31052, data="amount")

    return _ok(request_id, {"allow": True})


def create_transaction(params: dict, request_id) -> dict:
    """Create or return existing Payme transaction."""
    payme_id = params.get("id")          # Payme's transaction id
    account = params.get("account", {})
    order_id = account.get("order_id")
    amount = int(params.get("amount", 0))
    create_time = params.get("time")     # ms timestamp

    try:
        from apps.orders.models import Order
        order = Order.objects.get(id=order_id)
    except Exception:
        return _error(request_id, -31050, data="order_id")

    # Check if already paid
    if order.payment_status == "paid":
        return _error(request_id, -31061)

    # Validate amount
    expected_tiyin = int(order.total_amount * 100)
    if amount != expected_tiyin:
        return _error(request_id, -31052, data="amount")

    # Check if transaction already exists for this payme_id
    existing = PaymentTransaction.objects.filter(
        provider="payme",
        extra__payme_id=payme_id,
    ).first()

    if existing:
        if existing.extra.get("state") == STATE_CANCELLED:
            return _error(request_id, -31062)
        return _ok(request_id, {
            "create_time": existing.extra.get("create_time"),
            "perform_time": existing.extra.get("perform_time", 0),
            "cancel_time": existing.extra.get("cancel_time", 0),
            "transaction": str(existing.id),
            "state": existing.extra.get("state", STATE_CREATED),
            "receivers": None,
        })

    # Create new transaction
    txn = PaymentTransaction.objects.create(
        order=order,
        provider="payme",
        provider_transaction_id=payme_id,
        amount=Decimal(amount) / 100,
        status=PaymentStatus.WAITING,
        extra={
            "payme_id": payme_id,
            "state": STATE_CREATED,
            "create_time": create_time,
            "perform_time": 0,
            "cancel_time": 0,
            "reason": None,
        },
    )

    return _ok(request_id, {
        "create_time": create_time,
        "perform_time": 0,
        "cancel_time": 0,
        "transaction": str(txn.id),
        "state": STATE_CREATED,
        "receivers": None,
    })


def perform_transaction(params: dict, request_id) -> dict:
    """Mark order as paid (Payme has confirmed payment)."""
    payme_id = params.get("id")

    try:
        txn = PaymentTransaction.objects.select_related("order").get(
            provider="payme",
            extra__payme_id=payme_id,
        )
    except PaymentTransaction.DoesNotExist:
        return _error(request_id, -31060)

    if txn.extra.get("state") == STATE_CANCELLED:
        return _error(request_id, -31062)

    if txn.extra.get("state") == STATE_COMPLETED:
        # Idempotent
        return _ok(request_id, {
            "transaction": str(txn.id),
            "perform_time": txn.extra.get("perform_time"),
            "state": STATE_COMPLETED,
        })

    perform_time = int(timezone.now().timestamp() * 1000)

    txn.status = PaymentStatus.PAID
    txn.paid_at = timezone.now()
    txn.extra["state"] = STATE_COMPLETED
    txn.extra["perform_time"] = perform_time
    txn.save(update_fields=["status", "paid_at", "extra", "updated_at"])

    from apps.payments.services import mark_order_paid
    mark_order_paid(txn.order, txn)

    logger.info("Payme payment performed for txn %s, order %s", txn.id, txn.order_id)

    return _ok(request_id, {
        "transaction": str(txn.id),
        "perform_time": perform_time,
        "state": STATE_COMPLETED,
    })


def cancel_transaction(params: dict, request_id) -> dict:
    """Cancel/refund a Payme transaction."""
    payme_id = params.get("id")
    reason = int(params.get("reason", REASON_UNKNOWN))

    try:
        txn = PaymentTransaction.objects.select_related("order").get(
            provider="payme",
            extra__payme_id=payme_id,
        )
    except PaymentTransaction.DoesNotExist:
        return _error(request_id, -31060)

    cancel_time = int(timezone.now().timestamp() * 1000)

    if txn.extra.get("state") == STATE_COMPLETED:
        # Already performed → cancel after complete
        state = STATE_CANCELLED_AFTER_COMPLETE
    else:
        state = STATE_CANCELLED

    txn.status = PaymentStatus.CANCELLED
    txn.extra["state"] = state
    txn.extra["cancel_time"] = cancel_time
    txn.extra["reason"] = reason
    txn.save(update_fields=["status", "extra", "updated_at"])

    logger.info("Payme transaction cancelled: txn=%s reason=%s state=%s", txn.id, reason, state)

    return _ok(request_id, {
        "transaction": str(txn.id),
        "cancel_time": cancel_time,
        "state": state,
    })


def check_transaction(params: dict, request_id) -> dict:
    """Return current state of a transaction."""
    payme_id = params.get("id")

    try:
        txn = PaymentTransaction.objects.get(
            provider="payme",
            extra__payme_id=payme_id,
        )
    except PaymentTransaction.DoesNotExist:
        return _error(request_id, -31060)

    return _ok(request_id, {
        "create_time": txn.extra.get("create_time"),
        "perform_time": txn.extra.get("perform_time", 0),
        "cancel_time": txn.extra.get("cancel_time", 0),
        "transaction": str(txn.id),
        "state": txn.extra.get("state", STATE_CREATED),
        "reason": txn.extra.get("reason"),
    })


def get_statement(params: dict, request_id) -> dict:
    """Return list of transactions in a time range (reconciliation)."""
    from_time = params.get("from")  # ms
    to_time = params.get("to")

    txns = PaymentTransaction.objects.filter(
        provider="payme",
        created_at__gte=timezone.datetime.fromtimestamp(from_time / 1000, tz=timezone.utc),
        created_at__lte=timezone.datetime.fromtimestamp(to_time / 1000, tz=timezone.utc),
    )

    transactions = []
    for txn in txns:
        transactions.append({
            "id": txn.extra.get("payme_id"),
            "time": txn.extra.get("create_time"),
            "amount": txn.amount_tiyin,
            "account": {"order_id": str(txn.order_id)},
            "create_time": txn.extra.get("create_time"),
            "perform_time": txn.extra.get("perform_time", 0),
            "cancel_time": txn.extra.get("cancel_time", 0),
            "transaction": str(txn.id),
            "state": txn.extra.get("state", STATE_CREATED),
            "reason": txn.extra.get("reason"),
            "receivers": None,
        })

    return _ok(request_id, {"transactions": transactions})


# Method dispatcher
PAYME_METHODS = {
    "CheckPerformTransaction": check_perform_transaction,
    "CreateTransaction": create_transaction,
    "PerformTransaction": perform_transaction,
    "CancelTransaction": cancel_transaction,
    "CheckTransaction": check_transaction,
    "GetStatement": get_statement,
}


def dispatch(body: dict, request_id, params: dict) -> dict:
    method = body.get("method")
    handler = PAYME_METHODS.get(method)
    if not handler:
        return _error(request_id, -32601)
    return handler(params, request_id)
