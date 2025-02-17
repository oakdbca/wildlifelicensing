from django.urls import re_path

from wildlifelicensing.apps.payments.views import (
    CheckoutApplicationView,
    ManualPaymentView,
    PaymentsReportView,
)

urlpatterns = [
    # TODO: Make sure user can view invoice via ledger api client then remove this
    # url(r'wl/invoice-pdf/(?P<reference>\d+)',InvoicePDFView.as_view(), name='invoice-pdf'),
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
