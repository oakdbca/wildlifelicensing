from django.conf import settings
from django.template import Library

register = Library()


@register.simple_tag()
def system_name():
    return settings.SYSTEM_NAME


@register.simple_tag()
def system_name_short():
    return settings.SYSTEM_NAME_SHORT


@register.simple_tag()
def support_email():
    return settings.SUPPORT_EMAIL


@register.simple_tag()
def dept_name():
    return settings.DEP_NAME


@register.simple_tag()
def dept_support_phone():
    return settings.DEP_PHONE_SUPPORT


@register.simple_tag()
def dept_postal_address_line_1():
    return settings.DEP_POSTAL_ADDRESS_LINE_1


@register.simple_tag()
def dept_postal_address_line_2():
    return settings.DEP_POSTAL_ADDRESS_LINE_2


@register.simple_tag()
def dept_postal_postcode():
    return settings.DEP_POSTAL_POSTCODE


@register.simple_tag()
def dept_state():
    return settings.DEP_STATE
