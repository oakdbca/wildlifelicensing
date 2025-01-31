from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.db import models
from django.urls import reverse_lazy
from reversion import revisions
from reversion.models import Version

from wildlifelicensing.apps.main import helpers
from wildlifelicensing.apps.main.helpers import is_assessor, is_customer, is_officer


class BaseAccessMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    The main goal of this base mixin is to handle the 'no permission'.
    If the user is authenticated it should throw a PermissionDenied (status 403), but if the user is not authenticated
    it should return to the login page.
    """

    login_url = reverse_lazy("home")
    permission_denied_message = "You don't have the permission to access this resource."
    raise_exception = True

    def handle_no_permission(self):
        user = self.request.user
        if not user.is_authenticated:
            self.raise_exception = False
        return super().handle_no_permission()

    def test_func(self):
        """
        Override this method for access.
        Must return True if the current user can access the view.
        """
        return False


class CustomerRequiredMixin(BaseAccessMixin):
    """
    An AccessMixin that check for user being a customer.
    See rules in 'is_customer' function
    """

    def test_func(self):
        return is_customer(self.request.user)


class OfficerRequiredMixin(BaseAccessMixin):
    """
    An AccessMixin that check for user being a WL Officer.
    See rules in 'is_officer' function
    """

    def test_func(self):
        return is_officer(self.request.user)


class AssessorRequiredMixin(BaseAccessMixin):
    """
    An AccessMixin that check for user being a WL Assessor.
    See rules in 'is_assessor' function
    """

    def test_func(self):
        return is_assessor(self.request.user)


class OfficerOrCustomerRequiredMixin(BaseAccessMixin):
    """
    An AccessMixin that check for user being a WL Officer or a customer.
    See rules in 'is_officer' and 'is_customer' functions
    """

    def test_func(self):
        user = self.request.user
        return is_officer(user) or is_customer(user)


class OfficerOrAssessorRequiredMixin(BaseAccessMixin):
    """
    An AccessMixin that check for user being a WL Officer or WL Assessor.
    See rules in 'is_officer' and 'is_assessor' functions
    """

    def test_func(self):
        user = self.request.user
        return is_officer(user) or is_assessor(user)


class RevisionedMixin(models.Model):
    """
    A model tracked by reversion through the save method.
    """

    def save(self, **kwargs):
        if kwargs.pop("no_revision", False):
            super().save(**kwargs)
        else:
            with revisions.create_revision():
                if "version_user" in kwargs:
                    revisions.set_user(kwargs.pop("version_user", None))
                if "version_comment" in kwargs:
                    revisions.set_comment(kwargs.pop("version_comment", ""))
                super().save(**kwargs)

    @property
    def created_date(self):
        return Version.objects.get_for_object(self).last().revision.date_created

    @property
    def modified_date(self):
        return Version.objects.get_for_object(self).first().revision.date_created

    class Meta:
        abstract = True


class InvoiceOwnerMixin:

    def belongs_to(self, user, group_name):
        return helpers.belongs_to(user, group_name)

    def is_payment_admin(self, user):
        return helpers.is_payment_admin(user)

    def check_owner(self, user):
        return self.get_object().order.user == user or self.is_payment_admin(user)

    def dispatch(self, request, *args, **kwargs):
        if not self.check_owner(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
