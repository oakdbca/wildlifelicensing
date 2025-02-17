from django.urls import re_path

from wildlifelicensing.apps.customer_management.views.customer import (
    CustomerLookupView,
    EditDetailsView,
    EditProfileView,
)
from wildlifelicensing.apps.customer_management.views.tables import (
    DataTableApplicationView,
    DataTableLicencesView,
    DataTableReturnsView,
)

urlpatterns = [
    re_path("^$", CustomerLookupView.as_view(), name="customer_lookup"),
    re_path("^([0-9]+)/$", CustomerLookupView.as_view(), name="customer_lookup"),
    re_path(
        "^([0-9]+)/edit_details/$",
        EditDetailsView.as_view(),
        name="edit_customer_details",
    ),
    re_path(
        "^([0-9]+)/edit_profile/$",
        EditProfileView.as_view(),
        name="edit_customer_profile",
    ),
    re_path(
        "^([0-9]+)/edit_profile/([0-9]+)/$",
        EditProfileView.as_view(),
        name="edit_customer_profile",
    ),
    # tables
    re_path(
        r"^data/applications/([0-9]+)/?$",
        DataTableApplicationView.as_view(),
        name="data_applications",
    ),
    re_path(
        r"^data/licences/([0-9]+)/?$",
        DataTableLicencesView.as_view(),
        name="data_licences",
    ),
    re_path(
        r"^data/returns/([0-9]+)/?$",
        DataTableReturnsView.as_view(),
        name="data_returns",
    ),
]
