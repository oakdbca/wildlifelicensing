import json
import os
from datetime import date

from dateutil.relativedelta import relativedelta
from django import forms
from django.conf import settings
from django.forms.widgets import SelectMultiple
from django_countries.widgets import CountrySelectWidget
from ledger_api_client.ledger_models import EmailUserRO as EmailUser

from wildlifelicensing.apps.main.models import (
    Address,
    CommunicationsLogEntry,
    Profile,
    Region,
    WildlifeLicence,
)


class BetterJSONField(forms.JSONField):
    """
    A form field for the JSONField.
    It fixes the double 'stringification', avoid the null text and indents the json (see prepare_value).
    """

    def __init__(self, *, decoder=None, **kwargs):
        kwargs.setdefault("widget", forms.Textarea(attrs={"cols": 80, "rows": 20}))
        self.decoder = decoder or json.JSONDecoder
        super().__init__(**kwargs)

    def prepare_value(self, value):
        if value is None:
            return ""
        if isinstance(value, str):
            # already a string
            return value
        else:
            return json.dumps(value, indent=4)


class IdentificationForm(forms.Form):
    VALID_FILE_TYPES = [
        "png",
        "jpg",
        "jpeg",
        "gif",
        "pdf",
        "PNG",
        "JPG",
        "JPEG",
        "GIF",
        "PDF",
    ]

    identification_file = forms.FileField(
        label="Image containing Identification",
        help_text="E.g. drivers licence, passport, proof-of-age",
    )

    def clean_identification_file(self):
        id_file = self.cleaned_data.get("identification_file")

        ext = os.path.splitext(str(id_file))[1][1:]

        if ext not in self.VALID_FILE_TYPES:
            raise forms.ValidationError(
                "Uploaded image must be of file type: %s"
                % ", ".join(self.VALID_FILE_TYPES)
            )

        return id_file


class SeniorCardForm(forms.Form):
    VALID_FILE_TYPES = IdentificationForm.VALID_FILE_TYPES

    senior_card = forms.FileField(
        label="Senior Card", help_text="A scan or a photo or your Senior Card"
    )

    def clean_identification_file(self):
        id_file = self.cleaned_data.get("senior_card")

        ext = os.path.splitext(str(id_file))[1][1:]

        if ext not in self.VALID_FILE_TYPES:
            raise forms.ValidationError(
                "Uploaded image must be of file type: %s"
                % ", ".join(self.VALID_FILE_TYPES)
            )

        return id_file


class IssueLicenceForm(forms.ModelForm):
    ccs = forms.CharField(
        required=False,
        label="CCs",
        help_text="A comma separated list of email addresses you want the licence email to be CC'ed",
    )

    start_date = forms.DateField(
        input_formats=[settings.DEFAULT_FORM_DATE_FORMAT],
        required=True,
        widget=forms.DateTimeInput(format=settings.DEFAULT_FORM_DATE_FORMAT),
    )
    end_date = forms.DateField(
        input_formats=[settings.DEFAULT_FORM_DATE_FORMAT],
        required=True,
        widget=forms.DateTimeInput(format=settings.DEFAULT_FORM_DATE_FORMAT),
    )

    class Meta:
        model = WildlifeLicence
        fields = [
            "start_date",
            "end_date",
            "is_renewable",
            "return_frequency",
            "regions",
            "purpose",
            "locations",
            "additional_information",
            "cover_letter_message",
        ]
        widgets = {
            "regions": SelectMultiple(attrs={"class": "d-none"}),
            "purpose": forms.Textarea(attrs={"cols": "40", "rows": "8"}),
            "locations": forms.Textarea(attrs={"cols": "40", "rows": "5"}),
            "additional_information": forms.Textarea(attrs={"cols": "40", "rows": "5"}),
            "cover_letter_message": forms.Textarea(attrs={"cols": "40", "rows": "5"}),
        }

    def __init__(self, *args, **kwargs):
        regions = kwargs.pop("regions", Region.objects.none())
        end_date = kwargs.pop("end_date", None)
        is_renewable = kwargs.pop("is_renewable", False)
        default_period = kwargs.pop("default_period", None)
        return_frequency = kwargs.pop(
            "return_frequency", WildlifeLicence.DEFAULT_FREQUENCY
        )
        locations = kwargs.pop("locations", "")
        purpose = kwargs.pop("purpose", "")
        additional_information = kwargs.pop("additional_information", "")
        cover_letter_message = kwargs.pop("cover_letter_message", "")

        skip_required = kwargs.pop("skip_required", False)

        super().__init__(*args, **kwargs)

        if skip_required:
            for field in self.fields.values():
                field.required = False
        else:
            # enforce required for some fields not required at the ledger (Licence) model level
            required = ["start_date", "end_date"]
            for field_name in required:
                field = self.fields.get(field_name)
                if field is not None:
                    field.required = True

        self.fields["is_renewable"].widget = forms.CheckboxInput()

        # if a licence instance has not been passed in nor any POST data (i.e. get version of form)
        if "instance" not in kwargs and len(args) == 0:
            today_date = date.today()

            self.fields["start_date"].initial = today_date.strftime(
                settings.DEFAULT_FORM_DATE_FORMAT
            )

            if end_date is not None:
                self.fields["end_date"].initial = end_date
            elif default_period is not None:
                end_date = today_date + relativedelta(days=default_period)

                self.fields["end_date"].initial = end_date.strftime(
                    settings.DEFAULT_FORM_DATE_FORMAT
                )

            self.fields["regions"].initial = regions
            self.fields["is_renewable"].initial = is_renewable
            self.fields["return_frequency"].initial = return_frequency
            self.fields["locations"].initial = locations
            self.fields["purpose"].initial = purpose
            self.fields["additional_information"].initial = additional_information
            self.fields["cover_letter_message"].initial = cover_letter_message

    def clean(self):
        cleaned_data = super().clean()

        end_date = cleaned_data.get("end_date")
        start_date = cleaned_data.get("start_date")
        if end_date is not None and start_date is not None and end_date < start_date:
            msg = "End date must be greater than start date"
            self.add_error("end_date", msg)


class CommunicationsLogEntryForm(forms.ModelForm):
    attachment = forms.FileField(required=False)

    class Meta:
        model = CommunicationsLogEntry
        fields = ["reference", "to", "fromm", "type", "subject", "text", "attachment"]

    def __init__(self, *args, **kwargs):
        to = kwargs.pop("to", None)
        fromm = kwargs.pop("fromm", None)
        reference = kwargs.pop("reference", None)

        super().__init__(*args, **kwargs)

        if to is not None:
            self.fields["to"].initial = to

        if fromm is not None:
            self.fields["fromm"].initial = fromm

        if reference is not None:
            self.fields["reference"].initial = reference


class AddressForm(forms.ModelForm):
    update = forms.BooleanField(
        required=False, label="Check this to update all linked profiles."
    )

    class Meta:
        model = Address
        fields = [
            "update",
            "line1",
            "line2",
            "line3",
            "locality",
            "state",
            "country",
            "postcode",
            "user",
        ]
        widgets = {"country": CountrySelectWidget(), "user": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        self.profiles = None
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.profiles = Profile.objects.filter(postal_address=self.instance)
            if len(self.profiles) == 1:
                self.fields.pop("update")
        else:
            self.fields.pop("update")

        if user is not None:
            self.fields["user"].initial = user

    def save(self, commit=True):
        try:
            if "update" in self.fields:
                if self.cleaned_data["update"]:
                    address = Address.objects.get(
                        user=self.instance.user, hash=self.instance.generate_hash()
                    )
                    self.profiles.update(postal_address=address)
                    return address
                else:
                    address = Address.objects.get(
                        user=self.instance.user, hash=self.instance.generate_hash()
                    )
                    return address

            address = Address.objects.get(
                user=self.instance.user, hash=self.instance.generate_hash()
            )
            return address
        except Address.DoesNotExist:
            if "update" in self.fields and not self.cleaned_data["update"]:
                self.instance.id = None
            return super().save(commit)


class ProfileBaseForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        """
        instance = kwargs.get("instance")
        if instance and instance.pk:
            self.fields['auth_identity'].initial = kwargs["instance"].auth_identity
            if instance.user and instance.user.email == instance.email:
                #the profile's email is the same as the user account email, it must be an email identity;
                self.fields['auth_identity'].widget.attrs['disabled'] = True
        """

    def clean(self):
        super().clean()
        # always create a email identity for profile email
        self.cleaned_data["auth_identity"] = True

    """
    def clean_auth_identity(self):
        if not self.cleaned_data.get("auth_identity", False):
            if self.instance.user and self.instance.user.email == self.cleaned_data["email"]:
                # the profile's email is the same as the user account email, it must be an email identity;
                return True
        return self.cleaned_data.get("auth_identity")
    """

    def save(self, commit=True):
        setattr(
            self.instance,
            "auth_identity",
            self.cleaned_data.get("auth_identity", False),
        )
        return super().save(commit)

    class Meta:
        model = Profile
        fields = "__all__"


class ProfileAdminForm(ProfileBaseForm):
    pass


class ProfileForm(ProfileBaseForm):
    # auth_identity = forms.BooleanField(required=False)
    class Meta:
        model = Profile
        fields = ["user", "name", "email", "institution"]
        widgets = {"user": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        initial_display_name = kwargs.pop("initial_display_name", None)
        initial_email = kwargs.pop("initial_email", None)

        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields["user"].initial = user

        if initial_display_name is not None:
            self.fields["name"].initial = initial_display_name

        if initial_email is not None:
            self.fields["email"].initial = initial_email


class EmailUserForm(forms.ModelForm):
    class Meta:
        model = EmailUser
        fields = [
            "email",
            "first_name",
            "last_name",
            "title",
            "dob",
            "phone_number",
            "mobile_number",
            "fax_number",
        ]

    def __init__(self, *args, **kwargs):
        email_required = kwargs.pop("email_required", True)

        super().__init__(*args, **kwargs)

        self.fields["email"].required = email_required

        # some form renderers use widget's is_required field to set required attribute for input element
        self.fields["email"].widget.is_required = email_required
