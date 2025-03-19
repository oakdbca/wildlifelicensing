from rest_framework import serializers

from wildlifelicensing.apps.main.models import Licence, LicenceType
from wildlifelicensing.apps.main.serializers import EmailUserWithoutAddressesSerializer
from wildlifelicensing.apps.returns.models import (
    Return,
    ReturnAmendmentRequest,
    ReturnLogEntry,
)


class LicenceTypeReturnSerializer(serializers.ModelSerializer):
    name = serializers.CharField()

    class Meta:
        model = LicenceType
        fields = ("name",)


class LicenceReturnSerializer(serializers.ModelSerializer):
    licence_type = LicenceTypeReturnSerializer()
    holder = EmailUserWithoutAddressesSerializer()

    class Meta:
        model = Licence
        fields = (
            "id",
            "licence_number",
            "licence_sequence",
            "licence_type",
            "holder",
        )


class ReturnSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="get_status_display")
    licence = LicenceReturnSerializer()

    class Meta:
        model = Return
        fields = (
            "id",
            "licence",
            "status",
            "lodgement_number",
            "lodgement_date",
            "due_date",
            "proxy_customer",
            "nil_return",
            "comments",
        )


class ReturnAmendmentRequestSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="get_status_display")

    class Meta:
        model = ReturnAmendmentRequest
        fields = "__all__"


class ReturnLogEntrySerializer(serializers.ModelSerializer):
    type = serializers.CharField(source="get_type_display")
    documents = serializers.SerializerMethodField()

    class Meta:
        model = ReturnLogEntry
        exclude = ("ret", "customer")

    def get_documents(self, obj):
        return [(str(document), document.file.url) for document in obj.documents.all()]
