import logging

from django.core.serializers.json import (  # to handle the datetime serialization
    DjangoJSONEncoder,
)
from django.db.models.fields.files import FieldFile
from django.utils.encoding import smart_str
from django_countries.fields import Country
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from rest_framework import serializers

from wildlifelicensing.apps.main.models import Address, Document, Profile, UserAddress

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


class EmailUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        exclude = (
            "residential_address",
            "postal_address",
            "billing_address",
        )


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        exclude = ("user",)


class AddressSerializer(serializers.ModelSerializer):
    # oscar_address_id = serializers.CharField(source="id")
    oscar_address = UserAddressSerializer()

    class Meta:
        model = Address
        exclude = ("user",)


class ProfileSerializer(serializers.ModelSerializer):
    user = EmailUserSerializer()
    postal_address = AddressSerializer()

    class Meta:
        model = Profile
        fields = "__all__"


class DocumentSerializer(serializers.Serializer):

    class Meta:
        model = Document
        fields = "__all__"


class EmailUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        fields = "__all__"


class EmailUserWithoutResidentialAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        exclude = ("residential_address",)


class EmailUserWithoutAddressesSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        exclude = ("residential_address", "postal_address", "billing_address")
