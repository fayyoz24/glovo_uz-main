"""
Click callback tests.
"""
import hashlib
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from apps.payments.providers.click import handle_complete, handle_prepare, _verify_sign


def _make_sign(data: dict, action: int, secret: str) -> str:
    click_trans_id = str(data.get("click_trans_id", ""))
    service_id = str(data.get("service_id", ""))
    merchant_trans_id = str(data.get("merchant_trans_id", ""))
    amount = str(data.get("amount", ""))
    sign_time = str(data.get("sign_time", ""))

    if action == 1:
        merchant_prepare_id = str(data.get("merchant_prepare_id", ""))
        raw = f"{click_trans_id}{service_id}{secret}{merchant_trans_id}{merchant_prepare_id}{amount}{action}{sign_time}"
    else:
        raw = f"{click_trans_id}{service_id}{secret}{merchant_trans_id}{amount}{action}{sign_time}"

    return hashlib.md5(raw.encode()).hexdigest()


@pytest.mark.django_db
class TestClickPrepare:
    def test_invalid_signature_returns_error(self, settings):
        settings.CLICK_MERCHANT_ID = "111"
        settings.CLICK_SERVICE_ID = "222"
        settings.CLICK_SECRET_KEY = "secret"
        settings.CLICK_MERCHANT_USER_ID = "333"
        settings.CLICK_RETURN_URL = "http://localhost/"

        data = {
            "click_trans_id": "12345",
            "service_id": "222",
            "merchant_trans_id": "some-uuid",
            "amount": "50000",
            "action": "0",
            "sign_time": "2024-01-01 12:00:00",
            "sign_string": "wrong_sign",
        }
        result = handle_prepare(data)
        assert result["error"] == -1

    def test_wrong_action_returns_error(self, settings):
        settings.CLICK_MERCHANT_ID = "111"
        settings.CLICK_SERVICE_ID = "222"
        settings.CLICK_SECRET_KEY = "secret"
        settings.CLICK_MERCHANT_USER_ID = "333"
        settings.CLICK_RETURN_URL = "http://localhost/"

        data = {"action": "1"}
        result = handle_prepare(data)
        assert result["error"] == -3
