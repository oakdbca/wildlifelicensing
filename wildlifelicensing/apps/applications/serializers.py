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
    class Meta:
        model = EmailUser
        exclude = (
            "residential_address",
            "postal_address",
            "billing_address",
        )


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
    class Meta:
        model = WildlifeLicenceType
        fields = "__all__"


class ApplicationSerializer(serializers.ModelSerializer):
    applicant = ApplicationApplicantSerializer()
    proxy_applicant = ApplicationApplicantSerializer()
    assigned_officer = ApplicationApplicantSerializer()
    applicant_profile = ApplicationProfileSerializer()
    licence_type = ApplicationWildlifeLicenceTypeSerializer()

    class Meta:
        model = Application
        fields = "__all__"
