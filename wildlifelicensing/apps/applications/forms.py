from django import forms

from wildlifelicensing.apps.applications.models import (
    AmendmentRequest,
    ApplicationDeclinedDetails,
    ApplicationLogEntry,
    IDRequest,
    ReturnsRequest,
)
from wildlifelicensing.apps.main.forms import CommunicationsLogEntryForm
from wildlifelicensing.apps.main.models import Profile


class ProfileSelectionForm(forms.Form):
    profile = forms.ModelChoiceField(queryset=Profile.objects.none(), empty_label=None)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user")

        selected_profile = None
        if "selected_profile" in kwargs:
            selected_profile = kwargs.pop("selected_profile")

        super().__init__(*args, **kwargs)

        self.fields["profile"].queryset = user.profiles.all()

        if selected_profile is not None:
            self.fields["profile"].initial = selected_profile
        else:
            self.fields["profile"].initial = user.profiles.first()


class IDRequestForm(forms.ModelForm):
    class Meta:
        model = IDRequest
        fields = ["application", "officer", "reason", "text"]
        widgets = {"application": forms.HiddenInput(), "officer": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        application = kwargs.pop("application", None)
        officer = kwargs.pop("officer", None)

        super().__init__(*args, **kwargs)

        if application is not None:
            self.fields["application"].initial = application

        if officer is not None:
            self.fields["officer"].initial = officer


class ReturnsRequestForm(forms.ModelForm):
    class Meta:
        model = ReturnsRequest
        fields = ["application", "officer", "reason", "text"]
        widgets = {"application": forms.HiddenInput(), "officer": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        application = kwargs.pop("application", None)
        officer = kwargs.pop("officer", None)

        super().__init__(*args, **kwargs)

        if application is not None:
            self.fields["application"].initial = application

        if officer is not None:
            self.fields["officer"].initial = officer


class AmendmentRequestForm(forms.ModelForm):
    class Meta:
        model = AmendmentRequest
        fields = ["application", "officer", "reason", "text"]
        widgets = {"application": forms.HiddenInput(), "officer": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        application = kwargs.pop("application", None)
        officer = kwargs.pop("officer", None)

        super().__init__(*args, **kwargs)

        if application is not None:
            self.fields["application"].initial = application

        if officer is not None:
            self.fields["officer"].initial = officer


class ApplicationLogEntryForm(CommunicationsLogEntryForm):
    class Meta:
        model = ApplicationLogEntry
        fields = ["to", "fromm", "type", "subject", "text", "attachment"]


class ApplicationDeclinedDetailsForm(forms.ModelForm):
    class Meta:
        model = ApplicationDeclinedDetails
        fields = ["application", "officer", "reason"]
        widgets = {"application": forms.HiddenInput(), "officer": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        application = kwargs.pop("application", None)
        officer = kwargs.pop("officer", None)

        super().__init__(*args, **kwargs)

        if application is not None:
            self.fields["application"].initial = application

        if officer is not None:
            self.fields["officer"].initial = officer
