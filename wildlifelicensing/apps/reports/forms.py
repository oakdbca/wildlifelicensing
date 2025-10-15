from datetime import date, datetime

from django import forms
from django.conf import settings
from django.forms.widgets import SelectMultiple

from wildlifelicensing.apps.main.models import Region


class ReportForm(forms.Form):
    from_date = forms.DateField(
        input_formats=[settings.DEFAULT_FORM_DATE_FORMAT],
        required=True,
        widget=forms.DateTimeInput(format=settings.DEFAULT_FORM_DATE_FORMAT),
    )
    to_date = forms.DateField(
        input_formats=[settings.DEFAULT_FORM_DATE_FORMAT],
        required=True,
        widget=forms.DateTimeInput(format=settings.DEFAULT_FORM_DATE_FORMAT),
    )
    regions = forms.ModelMultipleChoiceField(
        queryset=Region.objects.all(),
        required=False,
        widget=SelectMultiple(attrs={"class": "d-none"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = datetime.today()

        if today.month < 7:
            self.fields["from_date"].initial = date(today.year - 1, 7, 1)
            self.fields["to_date"].initial = date(today.year, 6, 30)
        else:
            self.fields["from_date"].initial = date(today.year, 7, 1)
            self.fields["to_date"].initial = date(today.year + 1, 6, 30)
