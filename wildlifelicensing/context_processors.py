import hashlib

from django.conf import settings
from ledger_api_client import utils as ledger_api_utils


def config(request):
    lt = ledger_api_utils.get_ledger_totals()

    checkouthash = None
    if "payment_model" in request.session and "payment_pk" in request.session:
        checkouthash = hashlib.sha256(
            str(
                str(request.session["payment_model"])
                + str(request.session["payment_pk"])
            ).encode("utf-8")
        ).hexdigest()

    return {
        "template_group": settings.TEMPLATE_GROUP,
        "template_title": settings.TEMPLATE_TITLE,
        "LEDGER_UI_URL": settings.LEDGER_UI_URL,
        "PAYMENT_SYSTEM_PREFIX": settings.PAYMENT_SYSTEM_PREFIX,
        "ledger_totals": lt,
        "checkouthash": checkouthash,
        "GIT_COMMIT_HASH": settings.GIT_COMMIT_HASH,
    }
