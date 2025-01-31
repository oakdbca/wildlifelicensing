from django.urls import re_path as url

from wildlifelicensing.apps.payments.views import (
    CheckoutApplicationView,
    InvoicePDFView,
    ManualPaymentView,
    PaymentsReportView,
)

urlpatterns = [
    url(
        r"wl/invoice-pdf/(?P<reference>\d+)",
        InvoicePDFView.as_view(),
        name="invoice-pdf",
    ),
    url(
        "^checkout_application/([0-9]+)/$",
        CheckoutApplicationView.as_view(),
        name="checkout_application",
    ),
    url(
        "^manual_payment/([0-9]+)/$", ManualPaymentView.as_view(), name="manual_payment"
    ),
    url("^payments_report/?$", PaymentsReportView.as_view(), name="payments_report"),
]
