"""
Click Up (click.uz) payment provider integration.

Click has two flows:
1. Prepare  — initial callback from Click to verify order (POST /click/prepare/)
2. Complete — final callback when payment is done (POST /click/complete/)

Docs: https://docs.click.uz/
"""

import hashlib
import logging
from decimal import Decimal

from django.conf import settings
from django.utils import timezone

from apps.payments.exceptions import InvalidSignatureError, PaymentProviderError
from apps.payments.models import PaymentStatus, PaymentTransaction

logger = logging.getLogger(__name__)


CLICK_ERROR_CODES = {
    0: "Success",
    -1: "SIGN CHECK FAILED",
    -2: "Incorrect parameter amount",
    -3: "Action not found",
    -4: "Already paid",
    -5: "User does not exist",
    -6: "Transaction does not exist",
    -7: "Failed to update user",
    -8: "Error in request from click",
    -9: "Transaction cancelled",
}


def _get_settings():
    return {
        "merchant_id": settings.CLICK_MERCHANT_ID,
        "service_id": settings.CLICK_SERVICE_ID,
        "secret_key": settings.CLICK_SECRET_KEY,
        "merchant_user_id": settings.CLICK_MERCHANT_USER_ID,
    }


def build_payment_url(transaction: PaymentTransaction) -> str:
    """
    Returns Click payment page URL.
    Customer is redirected here to complete payment.
    """
    cfg = _get_settings()
    amount_sum = int(transaction.amount)  # Click needs whole sum (not tiyin)
    return (
        f"https://my.click.uz/services/pay"
        f"?service_id={cfg['service_id']}"
        f"&merchant_id={cfg['merchant_id']}"
        f"&amount={amount_sum}"
        f"&transaction_param={transaction.id}"
        f"&return_url={settings.CLICK_RETURN_URL}"
    )


def _verify_sign(data: dict, action: int) -> bool:
    """
    Verify Click callback signature.
    sign_string for prepare: MD5(click_trans_id + service_id + SECRET_KEY + merchant_trans_id + amount + action + sign_time)
    sign_string for complete: MD5(click_trans_id + service_id + SECRET_KEY + merchant_trans_id + merchant_prepare_id + amount + action + sign_time)
    """
    cfg = _get_settings()
    secret = cfg["secret_key"]

    click_trans_id = str(data.get("click_trans_id", ""))
    service_id = str(data.get("service_id", ""))
    merchant_trans_id = str(data.get("merchant_trans_id", ""))
    amount = str(data.get("amount", ""))
    action = str(action)
    sign_time = str(data.get("sign_time", ""))

    if action == "1":  # complete
        merchant_prepare_id = str(data.get("merchant_prepare_id", ""))
        raw = f"{click_trans_id}{service_id}{secret}{merchant_trans_id}{merchant_prepare_id}{amount}{action}{sign_time}"
    else:  # prepare
        raw = f"{click_trans_id}{service_id}{secret}{merchant_trans_id}{amount}{action}{sign_time}"

    computed = hashlib.md5(raw.encode()).hexdigest()
    received = data.get("sign_string", "")
    return computed == received


def handle_prepare(data: dict) -> dict:
    """
    Click PREPARE callback handler.
    Called by Click to verify the order before charging.

    Returns dict that Click expects.
    """
    action = int(data.get("action", -1))
    if action != 0:
        return {"error": -3, "error_note": CLICK_ERROR_CODES[-3]}

    if not _verify_sign(data, 0):
        logger.warning("Click prepare: invalid signature. data=%s", data)
        return {"error": -1, "error_note": CLICK_ERROR_CODES[-1]}

    merchant_trans_id = data.get("merchant_trans_id")  # our PaymentTransaction.id

    try:
        txn = PaymentTransaction.objects.select_related("order").get(
            id=merchant_trans_id,
            provider="click",
        )
    except PaymentTransaction.DoesNotExist:
        return {"error": -5, "error_note": "Transaction not found"}

    if txn.order.payment_status == "paid":
        return {"error": -4, "error_note": CLICK_ERROR_CODES[-4]}

    # Verify amount
    received_amount = Decimal(str(data.get("amount", 0)))
    if abs(received_amount - txn.amount) > Decimal("1"):
        return {"error": -2, "error_note": CLICK_ERROR_CODES[-2]}

    # Save Click trans id and mark waiting
    txn.provider_transaction_id = str(data.get("click_trans_id", ""))
    txn.status = PaymentStatus.WAITING
    txn.raw_request = data
    txn.save(update_fields=["provider_transaction_id", "status", "raw_request", "updated_at"])

    return {
        "click_trans_id": data.get("click_trans_id"),
        "merchant_trans_id": merchant_trans_id,
        "merchant_prepare_id": str(txn.id),
        "error": 0,
        "error_note": "Success",
    }


def handle_complete(data: dict) -> dict:
    """
    Click COMPLETE callback handler.
    Called after successful payment confirmation.
    """
    action = int(data.get("action", -1))
    if action != 1:
        return {"error": -3, "error_note": CLICK_ERROR_CODES[-3]}

    if not _verify_sign(data, 1):
        logger.warning("Click complete: invalid signature. data=%s", data)
        return {"error": -1, "error_note": CLICK_ERROR_CODES[-1]}

    merchant_prepare_id = data.get("merchant_prepare_id")

    try:
        txn = PaymentTransaction.objects.select_related("order").get(
            id=merchant_prepare_id,
            provider="click",
        )
    except PaymentTransaction.DoesNotExist:
        return {"error": -6, "error_note": CLICK_ERROR_CODES[-6]}

    if txn.order.payment_status == "paid":
        return {"error": -4, "error_note": CLICK_ERROR_CODES[-4]}

    # Check click error code
    click_error = int(data.get("error", 0))
    if click_error < 0:
        txn.status = PaymentStatus.FAILED
        txn.raw_response = data
        txn.save(update_fields=["status", "raw_response", "updated_at"])
        logger.info("Click payment failed for txn %s, click_error=%s", txn.id, click_error)
        return {
            "click_trans_id": data.get("click_trans_id"),
            "merchant_trans_id": str(txn.id),
            "merchant_confirm_id": str(txn.id),
            "error": 0,
            "error_note": "Success",
        }

    # Mark as paid
    from apps.payments.services import mark_order_paid  # avoid circular import

    txn.status = PaymentStatus.PAID
    txn.raw_response = data
    txn.paid_at = timezone.now()
    txn.save(update_fields=["status", "raw_response", "paid_at", "updated_at"])

    mark_order_paid(txn.order, txn)

    logger.info("Click payment confirmed for txn %s, order %s", txn.id, txn.order_id)

    return {
        "click_trans_id": data.get("click_trans_id"),
        "merchant_trans_id": str(txn.id),
        "merchant_confirm_id": str(txn.id),
        "error": 0,
        "error_note": "Success",
    }
