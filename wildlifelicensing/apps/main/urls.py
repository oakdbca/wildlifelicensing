from django.urls import re_path
from django.views.generic.base import RedirectView, TemplateView

from wildlifelicensing.apps.main.views import (
    AddCommunicationsLogEntryView,
    CommunicationsLogListView,
    CreateProfilesView,
    EditProfilesView,
    LicenceRenewalPDFView,
    ListProfilesView,
    SearchCustomersView,
    getLedgerIdentificationFile,
    getLedgerSeniorCardFile,
    getPrivateFile,
)

urlpatterns = [
    re_path(
        r"contact-us/$",
        TemplateView.as_view(template_name="wl/contact_us.html"),
        name="contact_us",
    ),
    re_path(
        r"further-information/$",
        RedirectView.as_view(
            url="https://www.dpaw.wa.gov.au/plants-and-animals/licences-and-authorities"
        ),
        name="further_information",
    ),
    re_path(
        "^search_customers/$", SearchCustomersView.as_view(), name="search_customers"
    ),
    re_path("^profiles/$", ListProfilesView.as_view(), name="list_profiles"),
    re_path("^profiles/create/$", CreateProfilesView.as_view(), name="create_profile"),
    re_path("^profiles/edit/$", EditProfilesView.as_view(), name="edit_profile_prefix"),
    re_path(
        "^profiles/edit/([0-9]+)/$", EditProfilesView.as_view(), name="edit_profile"
    ),
    re_path(
        "^licence-renewal-pdf/([0-9]+)/$",
        LicenceRenewalPDFView.as_view(),
        name="licence_renewal_pdf",
    ),
    # general communications log
    re_path(
        "^add-log-entry/([0-9]+)/$",
        AddCommunicationsLogEntryView.as_view(),
        name="add_log_entry",
    ),
    re_path(
        "^log-list/([0-9]+)/$", CommunicationsLogListView.as_view(), name="log_list"
    ),
    re_path(r"^private-media/", getPrivateFile, name="view_private_file"),
    re_path(
        r"^ledger-private/identification/(?P<emailuser_id>\d+)",
        getLedgerIdentificationFile,
        name="view_ledger_identification_file",
    ),
    re_path(
        r"^ledger-private/senior-card/(?P<emailuser_id>\d+)",
        getLedgerSeniorCardFile,
        name="view_ledger_senior_card_file",
    ),
]
