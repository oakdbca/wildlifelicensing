from django import template
from django.conf import settings

from wildlifelicensing.apps.main import helpers

register = template.Library()


@register.filter()
def is_customer(user):
    return helpers.is_customer(user)


@register.filter()
def is_officer(user):
    return helpers.is_officer(user)


@register.simple_tag(takes_context=True)
def is_internal(context):
    # checks if user is a departmentuser and logged in via single sign-on
    request = context["request"]
    return helpers.is_internal(request)


@register.simple_tag
def is_deprecated():
    return settings.DEPRECATED
