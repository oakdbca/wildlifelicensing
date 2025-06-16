import logging

from django.conf import settings
from django.core.serializers.json import (  # to handle the datetime serialization
    DjangoJSONEncoder,
)
from django.db.models.fields.files import FieldFile
from django.utils.encoding import smart_str
from django_countries.fields import Country
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from rest_framework import serializers

from wildlifelicensing.apps.main.helpers import is_officer
from wildlifelicensing.apps.main.models import (
    Address,
    CommunicationsLogEntry,
    Document,
    NomosTaxonomy,
    Profile,
    UserAddress,
)

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
    display = serializers.SerializerMethodField()

    class Meta:
        model = Address
        exclude = ("user",)

    def get_display(self, obj):
        display_fields = [
            "line1",
            "line2",
            "line3",
            "locality",
            "state",
            "postcode",
            "country",
        ]
        display_address = ""
        for field in display_fields:
            if getattr(obj, field):
                display_address += str(getattr(obj, field)) + " "
        return display_address


class ProfileSerializer(serializers.ModelSerializer):
    pk = serializers.IntegerField(source="id", read_only=True)
    user = EmailUserSerializer()
    postal_address = AddressSerializer()

    class Meta:
        model = Profile
        fields = "__all__"


class DocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = "__all__"


class EmailUserSerializer(serializers.ModelSerializer):
    pk = serializers.IntegerField(source="id", read_only=True)
    acc_mgmt_url = serializers.SerializerMethodField()
    profiles = ProfileSerializer(many=True, read_only=True)

    class Meta:
        model = EmailUser
        fields = "__all__"

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["profiles"] = sorted(response["profiles"], key=lambda x: x["id"])
        return response

    def get_acc_mgmt_url(self, obj):
        request = self.context.get("request")
        if (
            settings.LEDGER_UI_URL
            and request
            and request.user
            and is_officer(request.user)
        ):
            return (
                settings.LEDGER_UI_URL
                + "/ledger/account-management/"
                + str(obj.id)
                + "/change/"
            )
        return ""


class EmailUserWithoutResidentialAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        exclude = ("residential_address",)


class EmailUserWithoutAddressesSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailUser
        exclude = ("residential_address", "postal_address", "billing_address")


class CommunicationsLogEntrySerializer(serializers.ModelSerializer):
    documents = serializers.SerializerMethodField()

    class Meta:
        model = CommunicationsLogEntry
        fields = "__all__"

    def get_documents(self, obj):
        return [(str(document), document.file.url) for document in obj.documents.all()]


class NomosTaxonomySerializer(serializers.ModelSerializer):
    class Meta:
        model = NomosTaxonomy
        fields = "__all__"
