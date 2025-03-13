import json
from decimal import Decimal

import requests
from django.conf import settings
from django.shortcuts import get_object_or_404
from ledger_api_client.ledger_models import Invoice

from wildlifelicensing.apps.main.models import Product
from wildlifelicensing.apps.main.serializers import WildlifeLicensingJSONEncoder
from wildlifelicensing.apps.payments.exceptions import PaymentException

PAYMENT_STATUS_PAID = "paid"
PAYMENT_STATUS_CC_READY = "cc_ready"
PAYMENT_STATUS_AWAITING = "awaiting"
PAYMENT_STATUS_NOT_REQUIRED = "not_required"
PAYMENT_STATUS_OVER_PAID = "over_paid"

PAYMENT_STATUSES = {
    PAYMENT_STATUS_PAID: "Paid",
    PAYMENT_STATUS_CC_READY: "Credit Card Ready",
    PAYMENT_STATUS_AWAITING: "Awaiting Payment",
    PAYMENT_STATUS_NOT_REQUIRED: "Payment Not Required",
}


def to_json(data):
    return json.dumps(data, cls=WildlifeLicensingJSONEncoder)


def generate_product_title_variants(licence_type):
    def __append_variant_codes(product_title, variant_group, current_variant_codes):
        if variant_group is None:
            variant_codes.append(product_title)
            return

        for variant in variant_group.variants.all():
            variant_code = f"{product_title} {variant.product_title}"

            __append_variant_codes(variant_code, variant_group.child, variant_codes)

    variant_codes = []

    __append_variant_codes(
        licence_type.product_title, licence_type.variant_group, variant_codes
    )

    return variant_codes


def generate_product_title(application):
    product_title = application.licence_type.product_title

    if application.variants.exists():
        product_title = "{} {}".format(
            product_title,
            " ".join(
                application.variants.through.objects.filter(application=application)
                .order_by("order")
                .values_list("variant__product_title", flat=True)
            ),
        )

    return product_title


def get_product(product_title):
    try:
        return Product.objects.get(title=product_title)
    except Product.DoesNotExist:
        return None
    except Product.MultipleObjectsReturned:
        return None


def is_licence_free(product_title):
    product = get_product(product_title)
    return True if product is None else product.free_of_charge


def get_licence_price(product_title):
    product = get_product(product_title)
    return Decimal("0.00") if product is None else product.price


def get_application_payment_status(application):
    """
    :param application:
    :return: One of PAYMENT_STATUS_PAID, PAYMENT_STATUS_CC_READY, PAYMENT_STATUS_AWAITING or PAYMENT_STATUS_NOT_REQUIRED
    """
    if not application.invoice_reference:
        return PAYMENT_STATUS_NOT_REQUIRED

    invoice = get_object_or_404(Invoice, reference=application.invoice_reference)

    if invoice.amount == Decimal("0.00"):
        return PAYMENT_STATUS_NOT_REQUIRED

    if invoice.balance < Decimal("0.00"):
        return PAYMENT_STATUS_OVER_PAID

    if invoice.balance == Decimal("0.00"):
        return PAYMENT_STATUS_PAID

    return PAYMENT_STATUS_AWAITING

    # TODO: Make sure new system can handle this scenario?
    # elif invoice.token:
    #     return PAYMENT_STATUS_CC_READY


def invoke_credit_card_payment(application):
    invoice = get_object_or_404(Invoice, reference=application.invoice_reference)

    if not invoice.token:
        raise PaymentException("Application invoice does have a credit payment token")

    try:
        txn = invoice.make_payment()
    except Exception as e:
        raise PaymentException(f"Payment was unsuccessful. Reason({e.message})")

    if get_application_payment_status(application) != PAYMENT_STATUS_PAID:
        raise PaymentException(f"Payment was unsuccessful. Reason({txn.response_txt})")


def get_ledger_invoice_pdf(invoice_reference):
    api_key = settings.LEDGER_API_KEY
    url = (
        settings.LEDGER_API_URL
        + "/ledgergw/invoice-pdf/"
        + api_key
        + "/"
        + invoice_reference
    )
    response = requests.get(url=url)

    if not response.ok:
        raise Exception(
            f"Error retrieving invoice PDF with reference {invoice_reference}"
        )

    return response
