from django.core.serializers.json import (
    DjangoJSONEncoder,  # to handle the datetime serialization
)
from django.db.models.fields.files import FieldFile


class WildlifeLicensingJSONEncoder(DjangoJSONEncoder):
    """
    DjangoJSONEncoder subclass that encode file file object as its URL and country object to its name
    """

    def default(self, o):
        if isinstance(o, FieldFile):
            return o.url
        else:
            try:
                result = super().default(o)
            except (ValueError, TypeError):
                # workaround for django __proxy__ objects
                result = str(o)
            return result
