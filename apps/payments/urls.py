from django.urls import path

from apps.payments import views

app_name = "payments"

urlpatterns = [
    # Customer-facing
    path("initiate/", views.InitiatePaymentView.as_view(), name="initiate"),
    path("transactions/", views.PaymentTransactionListView.as_view(), name="transaction-list"),
    path("transactions/<uuid:pk>/", views.PaymentTransactionDetailView.as_view(), name="transaction-detail"),
    path("cash/confirm/", views.ConfirmCashPaymentView.as_view(), name="cash-confirm"),

    # Refunds
    path("refund/", views.RefundRequestView.as_view(), name="refund-request"),
    path("refund/<uuid:pk>/process/", views.ProcessRefundView.as_view(), name="refund-process"),

    # Click provider callbacks (called by Click servers)
    path("click/prepare/", views.ClickPrepareView.as_view(), name="click-prepare"),
    path("click/complete/", views.ClickCompleteView.as_view(), name="click-complete"),

    # Payme provider callback (JSON-RPC, called by Payme servers)
    path("payme/", views.PaymeCallbackView.as_view(), name="payme-callback"),
]
