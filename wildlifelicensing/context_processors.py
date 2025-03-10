from django.conf import settings


def config(request):
    return {
        "template_group": settings.TEMPLATE_GROUP,
        "template_title": settings.TEMPLATE_TITLE,
        "LEDGER_UI_URL": settings.LEDGER_UI_URL,
        "PAYMENT_SYSTEM_PREFIX": settings.PAYMENT_SYSTEM_PREFIX,
    }
