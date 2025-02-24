import logging

from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from rest_framework import serializers

from wildlifelicensing.apps.applications.models import (
    Application,
    ApplicationLogEntry,
    ApplicationRequest,
    Assessment,
)
from wildlifelicensing.apps.main.helpers import render_user_name
from wildlifelicensing.apps.main.models import (
    AssessorGroup,
    Condition,
    Profile,
    WildlifeLicence,
    WildlifeLicenceType,
)
from wildlifelicensing.apps.main.serializers import EmailUserWithoutAddressesSerializer

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
        # TODO: ledger api client PrivateDocument model does
        # not have an upload field: return obj.identification2.upload.url if obj.identification2 else None
        return "TODO: ledger api client PrivateDocument model does not have an upload field"

    def get_senior_card2(self, obj):
        # TODO: ledger api client PrivateDocument model does
        # not have an upload field: return obj.senior_card2.upload.url if obj.senior_card2 else None
        return "TODO: ledger api client PrivateDocument model does not have an upload field"


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
        return [dc for dc in obj.default_conditions.order_by("defaultcondition__order")]


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


class AssessmentOfficerSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmailUser
        exclude = ("residential_address",)


class AssessmentAssessorGroupSerializer(serializers.ModelSerializer):
    members = AssessmentOfficerSerializer(many=True)

    class Meta:
        model = AssessorGroup
        exclude = ("residential_address",)


class AssessmentConditionSerializer(serializers.ModelSerializer):
    acceptance_status = serializers.CharField(source="get_acceptance_status_display")

    class Meta:
        model = Condition
        fields = ("acceptance_status", "id", "condition")


class AssessmentSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source="get_status_display")
    officer = AssessmentOfficerSerializer()
    assigned_assessor = AssessmentOfficerSerializer()
    assessor_group = serializers.SerializerMethodField()
    conditions = serializers.SerializerMethodField()

    class Meta:
        model = Assessment
        exclude = ("application", "applicationrequest_ptr")

    def get_assessor_group(self, obj):
        return obj.assessor


class ConditionSerializer(serializers.Serializer):
    class Meta:
        model = Condition
        fields = "__all__"


class ApplicationLogEntrySerializer(serializers.Serializer):
    type = serializers.CharField(source="get_type_display")
    documents = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationLogEntry
        exclude = ("application", "communicationslogentry_ptr", "customer", "staff")

    def get_documents(self, obj):
        return [(str(document), document.file.url) for document in obj.documents.all()]


class ApplicationUserActionSerializer(serializers.Serializer):
    who = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = ("who", "when", "what")

    def get_who(self, obj):
        return render_user_name(obj.who)


class ApplicationRequestSerializer(serializers.Serializer):
    application = ApplicationSerializer()
    officer = EmailUserWithoutAddressesSerializer()

    class Meta:
        model = ApplicationRequest
        fields = "__all__"


class AmendmentRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(source="get_reason_display")
    application = ApplicationSerializer()
    officer = EmailUserWithoutAddressesSerializer()
    applicationrequest_ptr = ApplicationRequestSerializer()

    class Meta:
        model = Application
        fields = "__all__"
