import logging

from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from rest_framework import serializers

from wildlifelicensing.apps.applications.models import (
    AmendmentRequest,
    Application,
    ApplicationLogEntry,
    ApplicationRequest,
    ApplicationUserAction,
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
from wildlifelicensing.apps.main.serializers import (
    AddressSerializer,
    CommunicationsLogEntrySerializer,
    EmailUserWithoutAddressesSerializer,
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
        # TODO: ledger api client PrivateDocument model does
        # not have an upload field: return obj.identification2.upload.url if obj.identification2 else None
        return "TODO: ledger api client PrivateDocument model does not have an upload field"

    def get_senior_card2(self, obj):
        # TODO: ledger api client PrivateDocument model does
        # not have an upload field: return obj.senior_card2.upload.url if obj.senior_card2 else None
        return "TODO: ledger api client PrivateDocument model does not have an upload field"


class ApplicationProfileSerializer(serializers.ModelSerializer):
    user = ApplicationApplicantSerializer()
    postal_address = AddressSerializer()

    class Meta:
        model = Profile
        fields = ("user", "email", "id", "institution", "name", "postal_address")


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
            ConditionSerializer(dc).data
            for dc in obj.default_conditions.order_by("defaultcondition__order")
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
        return [
            ConditionSerializer(ap.condition).data
            for ap in obj.applicationcondition_set.order_by("order")
        ]


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
        exclude = ("application",)

    def get_assessor_group(self, obj):
        return obj.assessor_group.name if obj.assessor_group else None

    def get_conditions(self, obj):
        return [
            {
                "acceptance_status": ac.get_acceptance_status_display(),
                "id": ac.condition.id,
                "condition": ConditionSerializer(ac.condition.condition).data,
            }
            for ac in obj.assessmentcondition_set.all()
        ]


class ConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Condition
        fields = "__all__"


class ApplicationLogEntrySerializer(serializers.ModelSerializer):
    communicationslogentry_ptr = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationLogEntry
        exclude = ("application", "customer", "staff")

    def get_communicationslogentry_ptr(self, obj):
        if not obj or not hasattr(obj, "communicationslogentry_ptr"):
            return None
        return CommunicationsLogEntrySerializer(obj.communicationslogentry_ptr).data


class ApplicationUserActionSerializer(serializers.ModelSerializer):
    who = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationUserAction
        fields = ("who", "when", "what")

    def get_who(self, obj):
        return render_user_name(obj.who)


class ApplicationRequestSerializer(serializers.ModelSerializer):
    application = ApplicationSerializer()
    officer = EmailUserWithoutAddressesSerializer()

    class Meta:
        model = ApplicationRequest
        fields = "__all__"


class AmendmentRequestSerializer(serializers.ModelSerializer):
    applicationrequest_ptr = serializers.SerializerMethodField()
    application = serializers.SerializerMethodField()

    class Meta:
        model = AmendmentRequest
        fields = "__all__"

    def get_applicationrequest_ptr(self, obj):
        if not obj:
            return None
        return ApplicationRequestSerializer(obj.applicationrequest_ptr).data

    def get_application(self, obj):
        if not obj or not hasattr(obj, "applicationrequest_ptr"):
            return None
        return ApplicationSerializer(obj.applicationrequest_ptr.application).data
