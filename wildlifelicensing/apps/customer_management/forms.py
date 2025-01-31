from django import forms
from ledger_api_client.ledger_models import EmailUserRO as EmailUser


class CustomerSearchForm(forms.Form):
    search = forms.CharField()


class CustomerDetailsForm(forms.ModelForm):

    class Meta:
        model = EmailUser
        fields = [
            "first_name",
            "last_name",
            "title",
            "dob",
            "email",
            "phone_number",
            "mobile_number",
            "fax_number",
            "character_flagged",
            "character_comments",
        ]
        widgets = {"character_comments": forms.Textarea(attrs={"rows": 2})}
