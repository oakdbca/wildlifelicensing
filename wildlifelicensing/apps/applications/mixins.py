import datetime

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from wildlifelicensing.apps.applications.models import Application, Assessment
from wildlifelicensing.apps.main.helpers import is_assessor, is_officer
from wildlifelicensing.apps.main.mixins import BaseAccessMixin
from wildlifelicensing.apps.main.models import AssessorGroupMembers


class UserCanEditApplicationMixin(BaseAccessMixin):
    """
    CBV mixin that check that the user is the applicant and that the status of the application is
    in editable mode.
    Officers can edit an application
    """

    def get_application(self):
        if self.args:
            return Application.objects.filter(pk=self.args[0]).first()
        else:
            return None

    def test_func(self):
        """
        implementation of the UserCanEditApplicationMixin test_func
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        if is_officer(user):
            return True
        application = self.get_application()
        if application is not None:
            return application.applicant == user and application.can_user_edit
        else:
            return True


class UserCanRenewApplicationMixin(BaseAccessMixin):
    """
    CBV mixin that check that the user is the applicant and that the application is renewable.
    Officers can edit an application
    """

    def get_application(self):
        if self.args:
            return Application.objects.filter(licence=self.args[0]).first()
        else:
            return None

    def test_func(self):
        """
        implementation of the UserCanRenewApplicationMixin test_func
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        if is_officer(user):
            return True
        application = self.get_application()
        if application is not None:
            if application.applicant != user:
                return False

            expiry_days = (application.licence.end_date - datetime.date.today()).days
            return expiry_days <= 30 and application.licence.is_renewable
        else:
            return False


class UserCanAmendApplicationMixin(BaseAccessMixin):
    """
    CBV mixin that check that the user is the applicant and that the application is amendable.

    If the user is not logged-in it redirects to the login page, else it throws a 403
    Officers can edit an application
    """

    def get_application(self):
        if self.args:
            return Application.objects.filter(licence=self.args[0]).first()
        else:
            return None

    def test_func(self):
        """
        implementation of the UserCanAmendApplicationMixin test_func
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        if is_officer(user):
            return True
        application = self.get_application()
        if application is not None:
            if application.applicant != user:
                return False
            return application.licence.end_date >= datetime.date.today()
        else:
            return False


class RedirectApplicationInSessionMixin:
    """
    Mixin to check if there is currently an application in the session and if so, redirect to home with a message. This
    is for the case when a view is about to start entering application details but another application is currently
    being entered.
    """

    def dispatch(self, request, *args, **kwargs):
        if "application_id" in request.session:
            messages.error(
                request,
                format_html(
                    "There is currently another application in the process of being entered. Please "
                    "conclude or save this application before creating a new one. If you are seeing this "
                    "message and there is not another application being entered, you may need to {}",
                    format_html(
                        '<a href="{}">logout</a> and log in again.', reverse("logout")
                    ),
                ),
            )
            return redirect("wl_home")

        return super().dispatch(request, *args, **kwargs)


class RedirectApplicationNotInSessionMixin:
    """
    Mixin to check if an application is in the session, and if not, redirect to home with a message. This is the case
    where an application is being edited but somehow the session has become corrupt and there is no longer an
    application referenced there.
    """

    def dispatch(self, request, *args, **kwargs):
        if "application_id" not in request.session:
            messages.error(request, "The application session was corrupted.")
            return redirect("wl_home")

        return super().dispatch(request, *args, **kwargs)


class CanPerformAssessmentMixin(BaseAccessMixin):
    """
    CBV mixin that check the 'editability' of assessment that the user is a assesso
    and that he/she belongs to the right assessor group.
    This mixin assume that the url contains the pk of the assessment in 2nd position
    """

    def get_assessment(self):
        if len(self.args) > 1:
            return Assessment.objects.filter(pk=self.args[1]).first()
        else:
            return None

    def test_func(self):
        """
        implementation of the UserPassesTestMixin test_func
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if not is_assessor(user):
            return False
        assessment = self.get_assessment()
        return (
            assessment is not None
            and AssessorGroupMembers.objects.filter(
                assessorgroup=assessment.assessor_group, emailuser_id=user.id
            ).exists()  # assessment.assessor_group in get_user_assessor_groups(user)
        )


class UserCanViewApplicationMixin(BaseAccessMixin):
    """
    CBV mixin that check that the user is the applicant or an officer and that the status of the
    application is in approved mode.
    """

    def get_application(self):
        if self.args:
            return Application.objects.filter(pk=self.args[0]).first()
        else:
            return None

    def test_func(self):
        """
        implementation of the UserPassesTestMixin test_func
        """
        user = self.request.user
        if not user.is_authenticated:
            return False
        if is_officer(user) or is_assessor(user):
            return True
        application = self.get_application()
        if application is not None:
            return application.applicant == user and application.can_user_view
        else:
            return True
