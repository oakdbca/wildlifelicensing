from django.template import Library
from django.conf import settings
from wildlifelicensing.apps.main import helpers

register = Library()


@register.filter(name='is_customer')
def is_customer(user):
    return helpers.is_customer(user)


@register.filter(name='is_officer')
def is_officer(user):
    return helpers.is_officer(user)


#@register.filter(name='is_deprecated')
@register.simple_tag
def is_deprecated():
    return settings.DEPRECATED

