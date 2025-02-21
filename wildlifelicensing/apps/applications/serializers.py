import logging

from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from rest_framework import serializers

from wildlifelicensing.apps.applications.models import Application
from wildlifelicensing.apps.main.models import (
    Profile,
    WildlifeLicence,
    WildlifeLicenceType,
)

logger = logging.getLogger(__name__)


class ApplicationApplicantSerializer(serializers.ModelSerializer):
    identification2 = serializers.SerializerMethodField()
    senior_card2 = serializers.SerializerMethodField()

    class Meta:
        model = EmailUser
        exclude = (
            "residential_address",
            "postal_address",
            "billing_address",
        )

    def get_identification2(self, obj):
        return obj.identification2.upload.url if obj.identification2 else None

    def get_senior_card2(self, obj):
        return obj.senior_card2.upload.url if obj.senior_card2 else None


class ApplicationProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("email", "id", "institution", "name")


class PreviousApplicationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Application
        exclude = (
            "applicant",
            "applicant_profile",
            "previous_application",
            "licence",
            "proxy_applicant",
            "assigned_officer",
        )


class ApplicationLicenceProfileSerializer(serializers.ModelSerializer):
    user = ApplicationApplicantSerializer()

    class Meta:
        model = Profile
        fields = "user"


class ApplicationLicenceSerializer(serializers.ModelSerializer):
    holder = ApplicationApplicantSerializer()
    issuer = ApplicationApplicantSerializer()
    profile = ApplicationLicenceProfileSerializer()

    class Meta:
        model = WildlifeLicence
        exclude = (
            "holder",
            "issuer",
            "profile",
            "licence_ptr",
            "replaced_by",
        )


class ApplicationWildlifeLicenceTypeSerializer(serializers.ModelSerializer):
    default_conditions = serializers.SerializerMethodField()

    class Meta:
        model = WildlifeLicenceType
        fields = "__all__"

    def get_default_conditions(self, obj):
        return [
            ap.condition
            for ap in obj.licence_type.defaultcondition_set.order_by("order")
        ]


class ApplicationSerializer(serializers.ModelSerializer):
    applicant = ApplicationApplicantSerializer()
    proxy_applicant = ApplicationApplicantSerializer()
    assigned_officer = ApplicationApplicantSerializer()
    applicant_profile = ApplicationProfileSerializer()
    licence_type = ApplicationWildlifeLicenceTypeSerializer()
    processing_status = serializers.CharField(source="get_processing_status_display")
    id_check_status = serializers.CharField(source="get_id_check_status_display")
    returns_check_status = serializers.CharField(
        source="get_returns_check_status_display"
    )
    character_check_status = serializers.CharField(
        source="get_character_check_status_display"
    )
    review_status = serializers.CharField(source="get_review_status_display")
    conditions = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = "__all__"

    def get_conditions(self, obj):
        return [ap.condition for ap in obj.applicationcondition_set.order_by("order")]
