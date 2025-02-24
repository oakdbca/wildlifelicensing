from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView, View

from wildlifelicensing.apps.applications.forms import ApplicationLogEntryForm
from wildlifelicensing.apps.applications.mixins import (
    CanPerformAssessmentMixin,
    UserCanViewApplicationMixin,
)
from wildlifelicensing.apps.applications.models import (
    Application,
    ApplicationDeclinedDetails,
    ApplicationLogEntry,
    ApplicationUserAction,
    Assessment,
)
from wildlifelicensing.apps.applications.pdf import create_application_pdf_bytes
from wildlifelicensing.apps.applications.serializers import (
    ApplicationLogEntrySerializer,
    ApplicationSerializer,
    ApplicationUserActionSerializer,
    AssessmentSerializer,
)
from wildlifelicensing.apps.applications.utils import (
    append_app_document_to_schema_data,
    convert_documents_to_url,
    get_log_entry_to,
)
from wildlifelicensing.apps.main.helpers import is_officer, render_user_name
from wildlifelicensing.apps.main.mixins import OfficerOrAssessorRequiredMixin
from wildlifelicensing.apps.main.models import Document
from wildlifelicensing.apps.main.serializers import WildlifeLicensingJSONEncoder
from wildlifelicensing.apps.payments import utils as payment_utils


class ViewReadonlyView(UserCanViewApplicationMixin, TemplateView):
    template_name = "wl/view/view_readonly.html"

    def get_context_data(self, **kwargs):
        application = get_object_or_404(Application, pk=self.args[0])

        if application.hard_copy is not None:
            application.licence_type.application_schema, application.data = (
                append_app_document_to_schema_data(
                    application.licence_type.application_schema,
                    application.data,
                    application.hard_copy.file.url,
                )
            )

        convert_documents_to_url(application.data, application.documents.all(), "")

        kwargs["application"] = ApplicationSerializer(application).data

        if is_officer(self.request.user):
            kwargs["customer"] = application.applicant

            kwargs["log_entry_form"] = ApplicationLogEntryForm(
                to=get_log_entry_to(application),
                fromm=self.request.user.get_full_name(),
            )
        else:
            kwargs["payment_status"] = payment_utils.PAYMENT_STATUSES.get(
                payment_utils.get_application_payment_status(application)
            )
        if application.processing_status == "declined":
            message = "This application has been declined."
            details = ApplicationDeclinedDetails.objects.filter(
                application=application
            ).first()
            if details and details.reason:
                message += "<br/>Reason:<br/>{}".format(
                    details.reason.replace("\n", "<br/>")
                )
                kwargs["application"]["declined_reason"] = details.reason
            messages.error(self.request, message)

        return super().get_context_data(**kwargs)


class ViewPDFView(UserCanViewApplicationMixin, View):
    def get(self, request, *args, **kwargs):
        application = get_object_or_404(Application, pk=self.args[0])

        response = HttpResponse(content_type="application/pdf")

        response.write(create_application_pdf_bytes(application))

        return response


class ViewReadonlyOfficerView(UserCanViewApplicationMixin, TemplateView):
    template_name = "wl/view/view_readonly_officer.html"

    def get_context_data(self, **kwargs):
        application = get_object_or_404(Application, pk=self.args[0])

        if application.hard_copy is not None:
            application.licence_type.application_schema, application.data = (
                append_app_document_to_schema_data(
                    application.licence_type.application_schema,
                    application.data,
                    application.hard_copy.file.url,
                )
            )

        convert_documents_to_url(application.data, application.documents.all(), "")

        kwargs["application"] = ApplicationSerializer(application).data

        kwargs["assessments"] = AssessmentSerializer(
            Assessment.objects.filter(application=application), many=True
        ).data

        kwargs["payment_status"] = payment_utils.PAYMENT_STATUSES.get(
            payment_utils.get_application_payment_status(application)
        )

        kwargs["log_entry_form"] = ApplicationLogEntryForm(
            to=get_log_entry_to(application), fromm=self.request.user.get_full_name()
        )

        if application.processing_status == "declined":
            details = ApplicationDeclinedDetails.objects.filter(
                application=application
            ).first()
            if details and details.reason:
                kwargs["application"]["declined_reason"] = details.reason
        return super().get_context_data(**kwargs)


class ViewReadonlyAssessorView(CanPerformAssessmentMixin, TemplateView):
    template_name = "wl/view/view_readonly_assessor.html"

    def get_context_data(self, **kwargs):
        application = get_object_or_404(Application, pk=self.args[0])

        if application.hard_copy is not None:
            application.licence_type.application_schema, application.data = (
                append_app_document_to_schema_data(
                    application.licence_type.application_schema,
                    application.data,
                    application.hard_copy.file.url,
                )
            )

        convert_documents_to_url(application.data, application.documents.all(), "")

        kwargs["application"] = ApplicationSerializer(application).data

        kwargs["form_structure"] = application.licence_type.application_schema

        assessment = get_object_or_404(Assessment, pk=self.args[1])

        kwargs["assessment"] = AssessmentSerializer(assessment).data

        kwargs["other_assessments"] = AssessmentSerializer(
            Assessment.objects.filter(application=application)
            .exclude(id=assessment.id)
            .order_by("id"),
            many=True,
        ).data

        kwargs["log_entry_form"] = ApplicationLogEntryForm(
            to=get_log_entry_to(application), fromm=self.request.user.get_full_name()
        )

        if application.processing_status == "declined":
            message = "This application has been declined."
            details = ApplicationDeclinedDetails.objects.filter(
                application=application
            ).first()
            if details and details.reason:
                message += "<br/>Reason:<br/>{}".format(
                    details.reason.replace("\n", "<br/>")
                )
                kwargs["application"]["declined_reason"] = details.reason
            messages.error(self.request, message)

        return super().get_context_data(**kwargs)


class ApplicationLogListView(OfficerOrAssessorRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        application = get_object_or_404(Application, pk=args[0])
        data = ApplicationLogEntrySerializer(
            ApplicationLogEntry.objects.filter(application=application)
        ).data
        return JsonResponse(
            {"data": data}, safe=False, encoder=WildlifeLicensingJSONEncoder
        )


class AddApplicationLogEntryView(OfficerOrAssessorRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = ApplicationLogEntryForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            application = get_object_or_404(Application, pk=args[0])

            customer = application.applicant

            staff = request.user

            kwargs = {
                "staff": staff,
                "customer": customer,
                "application": application,
                "type": form.cleaned_data["type"],
                "text": form.cleaned_data["text"],
                "subject": form.cleaned_data["subject"],
                "to": form.cleaned_data["to"],
                "fromm": form.cleaned_data["fromm"],
            }

            entry = ApplicationLogEntry.objects.create(**kwargs)
            if request.FILES and "attachment" in request.FILES:
                document = Document.objects.create(file=request.FILES["attachment"])
                entry.documents.add(document)

            return JsonResponse("ok", safe=False, encoder=WildlifeLicensingJSONEncoder)
        else:
            return JsonResponse(
                {
                    "errors": [
                        {
                            "status": "422",
                            "title": "Data not valid",
                            "detail": form.errors,
                        }
                    ]
                },
                safe=False,
                encoder=WildlifeLicensingJSONEncoder,
                status_code=422,
            )


class ApplicationUserActionListView(OfficerOrAssessorRequiredMixin, View):
    serial_template = {
        "fields": ["who", "when", "what"],
        "related": {"who": {"posthook": render_user_name}},
    }

    def get(self, request, *args, **kwargs):
        application = get_object_or_404(Application, pk=args[0])
        data = ApplicationUserActionSerializer(
            ApplicationUserAction.objects.filter(application=application), many=True
        ).data
        return JsonResponse(
            {"data": data}, safe=False, encoder=WildlifeLicensingJSONEncoder
        )
