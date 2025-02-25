from django.conf import settings


def config(request):
    return {
        "template_group": settings.TEMPLATE_GROUP,
        "template_title": settings.TEMPLATE_TITLE,
    }
