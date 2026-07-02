"""
Payment services — business logic layer.

Pattern: thin views → services → models
"""

import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.payments.exceptions import OrderAlreadyPaid, PaymentError, RefundNotAllowed
from apps.payments.models import (
    PaymentProvider,
    PaymentStatus,
    PaymentTransaction,
    Refund,
    RefundStatus,
)

logger = logging.getLogger(__name__)


def initiate_payment(order, provider: str) -> PaymentTransaction:
    """
    Create a PaymentTransaction and return it (with payment_url for redirect providers).
    Cash orders are immediately marked as pending.
    """
    if order.payment_status == "paid":
        raise OrderAlreadyPaid("Bu buyurtma allaqachon to'langan.")

    if provider not in PaymentProvider.values:
        raise PaymentError(f"Noma'lum payment provider: {provider}")

    if provider == PaymentProvider.CASH:
        txn = PaymentTransaction.objects.create(
            order=order,
            provider=provider,
            amount=order.total_amount,
            currency="UZS",
            status=PaymentStatus.PENDING,
        )
        return txn

    # Online providers: Click or Payme
    with transaction.atomic():
        txn = PaymentTransaction.objects.create(
            order=order,
            provider=provider,
            amount=order.total_amount,
            currency="UZS",
            status=PaymentStatus.PENDING,
        )

        if provider == PaymentProvider.CLICK:
            from apps.payments.providers.click import build_payment_url
            txn.payment_url = build_payment_url(txn)

        elif provider == PaymentProvider.PAYME:
            from apps.payments.providers.payme import build_payment_url
            txn.payment_url = build_payment_url(txn)

        txn.save(update_fields=["payment_url"])

    logger.info("Payment initiated: txn=%s order=%s provider=%s", txn.id, order.id, provider)
    return txn


@transaction.atomic
def mark_order_paid(order, txn: PaymentTransaction):
    """
    Called by Click/Payme callbacks after successful payment.
    Updates order payment_status → paid, saves timestamp.
    """
    # Re-fetch with lock
    from apps.orders.models import Order  # avoid circular import

    order = Order.objects.select_for_update().get(id=order.id)

    if order.payment_status == "paid":
        logger.warning("Order %s already paid, skipping mark_order_paid", order.id)
        return

    order.payment_status = "paid"
    order.save(update_fields=["payment_status", "updated_at"])

    logger.info(
        "Order %s marked as paid via %s (txn=%s)",
        order.id,
        txn.provider,
        txn.id,
    )

    # Trigger notification async
    try:
        from apps.notifications.tasks import send_payment_success_notification
        send_payment_success_notification.delay(str(order.id))
    except Exception as e:
        logger.warning("Could not send payment notification: %s", e)


def confirm_cash_payment(order) -> PaymentTransaction:
    """
    Admin/courier confirms cash was received.
    """
    txn = (
        PaymentTransaction.objects.filter(order=order, provider=PaymentProvider.CASH)
        .order_by("-created_at")
        .first()
    )
    if not txn:
        raise PaymentError("Cash transaction topilmadi.")

    if txn.status == PaymentStatus.PAID:
        raise OrderAlreadyPaid("Allaqachon to'langan.")

    with transaction.atomic():
        txn.status = PaymentStatus.PAID
        txn.paid_at = timezone.now()
        txn.save(update_fields=["status", "paid_at", "updated_at"])
        mark_order_paid(order, txn)

    return txn


def request_refund(order, amount: Decimal, reason: str) -> Refund:
    """
    Create a refund request. Actual processing happens in process_refund.
    """
    paid_txn = PaymentTransaction.objects.filter(
        order=order,
        status=PaymentStatus.PAID,
    ).order_by("-paid_at").first()

    if not paid_txn:
        raise RefundNotAllowed("To'langan transaction topilmadi.")

    total_refunded = (
        Refund.objects.filter(
            order=order,
            status__in=[RefundStatus.APPROVED, RefundStatus.PROCESSED],
        )
        .aggregate(total=Sum("amount"))
        .get("total") or Decimal("0")
    )

    if total_refunded + amount > paid_txn.amount:
        raise RefundNotAllowed("Refund miqdori to'langan summadan oshib ketdi.")

    refund = Refund.objects.create(
        order=order,
        transaction=paid_txn,
        amount=amount,
        reason=reason,
        status=RefundStatus.PENDING,
    )

    logger.info("Refund requested: refund=%s order=%s amount=%s", refund.id, order.id, amount)
    return refund


@transaction.atomic
def process_refund(refund: Refund):
    """
    Actually call provider's refund API.
    For Payme: CancelTransaction
    For Click: separate refund API call
    For Cash: manual (just mark as processed)
    """
    if refund.status != RefundStatus.PENDING:
        raise RefundNotAllowed("Bu refund qayta ishlanmoqda yoki allaqachon yakunlangan.")

    txn = refund.transaction
    provider = txn.provider

    try:
        if provider == PaymentProvider.CASH:
            # Cash returns: just mark as processed (physical cash return)
            refund.status = RefundStatus.PROCESSED
            refund.processed_at = timezone.now()
            refund.provider_response = {"note": "Cash refund — manual"}
            refund.save()

        elif provider == PaymentProvider.PAYME:
            _process_payme_refund(refund, txn)

        elif provider == PaymentProvider.CLICK:
            _process_click_refund(refund, txn)

        logger.info("Refund processed: refund=%s provider=%s", refund.id, provider)

    except Exception as e:
        refund.status = RefundStatus.REJECTED
        refund.provider_response = {"error": str(e)}
        refund.save(update_fields=["status", "provider_response", "updated_at"])
        raise


def _process_payme_refund(refund: Refund, txn: PaymentTransaction):
    """
    Payme refund = CancelTransaction after perform.
    Payme handles partial refunds via their dashboard; API only allows full cancel.
    """
    # Payme doesn't support partial refunds via API directly.
    # Full cancel after perform → STATE_CANCELLED_AFTER_COMPLETE
    # For partial, use Payme merchant cabinet.
    refund.status = RefundStatus.APPROVED
    refund.processed_at = timezone.now()
    refund.provider_response = {
        "note": "Payme refund must be processed via Payme merchant cabinet for partial amounts"
    }
    refund.save(update_fields=["status", "processed_at", "provider_response", "updated_at"])


def _process_click_refund(refund: Refund, txn: PaymentTransaction):
    """
    Click refund via Click API.
    Requires Click merchant API key (separate from service key).
    """
    import hashlib
    import requests
    from django.conf import settings

    # Click refund endpoint
    url = "https://api.click.uz/v2/merchant/payment/reversal/"
    merchant_id = settings.CLICK_MERCHANT_ID
    merchant_user_id = settings.CLICK_MERCHANT_USER_ID
    secret_key = settings.CLICK_SECRET_KEY

    timestamp = int(timezone.now().timestamp())
    sign_string = f"{merchant_id}{txn.provider_transaction_id}{secret_key}{timestamp}"
    sign = hashlib.sha1(sign_string.encode()).hexdigest()

    payload = {
        "merchant_id": merchant_id,
        "merchant_user_id": merchant_user_id,
        "payment_id": txn.provider_transaction_id,
        "reason": refund.reason[:100],
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Auth": f"{merchant_user_id}:{sign}:{timestamp}",
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    data = resp.json()

    if data.get("error_code") == 0:
        refund.status = RefundStatus.PROCESSED
        refund.processed_at = timezone.now()
    else:
        refund.status = RefundStatus.REJECTED
    refund.provider_response = data
    refund.save(update_fields=["status", "processed_at", "provider_response", "updated_at"])


def get_transaction_list(order):
    return PaymentTransaction.objects.filter(order=order).order_by("-created_at")


def get_transaction_detail(transaction_id, user=None):
    qs = PaymentTransaction.objects.select_related("order")
    if user and not user.is_staff:
        qs = qs.filter(order__customer=user)
    return qs.get(id=transaction_id)
