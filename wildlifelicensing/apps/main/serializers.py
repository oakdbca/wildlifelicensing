import logging

from django.core.serializers.json import (  # to handle the datetime serialization
    DjangoJSONEncoder,
)
from django.db.models.fields.files import FieldFile
from django.utils.encoding import smart_str
from django_countries.fields import Country

logger = logging.getLogger(__name__)


class WildlifeLicensingJSONEncoder(DjangoJSONEncoder):
    """
    DjangoJSONEncoder subclass that encode file file object as its URL and country object to its name
    """

    def default(self, o):
        if isinstance(o, FieldFile):
            return o.url
        elif isinstance(o, Country):
            return smart_str(o.name)
        else:
            try:
                result = super().default(o)
            except Exception as e:
                # workaround for django __proxy__ objects
                logger.warning("Failed to serialize object of type %s: %s", type(o), e)
                result = str(o)
            return result
