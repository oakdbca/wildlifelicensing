from django.urls import re_path

from wildlifelicensing.apps.payments.views import (
    CheckoutApplicationView,
    InvoicePDFView,
    ManualPaymentView,
    PaymentsReportView,
    PaymentSuccessView,
)

urlpatterns = [
    re_path(
        r"ledger-api-payment-success-callback/(?P<payment_uuid>.+)/",
        PaymentSuccessView.as_view(),
        name="ledger-api-payment-success-callback",
    ),
    re_path(
        r"wl/invoice-pdf/(?P<invoice_reference>\d+)",
        InvoicePDFView.as_view(),
        name="invoice-pdf",
    ),
    re_path(
        "^checkout_application/([0-9]+)/$",
        CheckoutApplicationView.as_view(),
        name="checkout_application",
    ),
    re_path(
        "^manual_payment/([0-9]+)/$", ManualPaymentView.as_view(), name="manual_payment"
    ),
    re_path(
        "^payments_report/?$", PaymentsReportView.as_view(), name="payments_report"
    ),
]
