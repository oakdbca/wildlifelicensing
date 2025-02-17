from django.urls import re_path

from wildlifelicensing.apps.dashboard.views import assessor, base, customer, officer

urlpatterns = [
    re_path(r"^dashboard/?$", base.DashBoardRoutingView.as_view(), name="home"),
    re_path(
        r"^dashboard/officer/?$",
        officer.DashboardOfficerTreeView.as_view(),
        name="tree_officer",
    ),
    re_path(
        r"^dashboard/tables/customer/?$",
        customer.TableCustomerView.as_view(),
        name="tables_customer",
    ),
    re_path(
        r"^dashboard/tables/assessor/?$",
        assessor.TableAssessorView.as_view(),
        name="tables_assessor",
    ),
    # Applications
    re_path(
        r"^dashboard/tables/applications/officer/?$",
        officer.TablesApplicationsOfficerView.as_view(),
        name="tables_applications_officer",
    ),
    re_path(
        r"^dashboard/data/applications/officer/?$",
        officer.DataTableApplicationsOfficerView.as_view(),
        name="data_application_officer",
    ),
    re_path(
        r"^dashboard/tables/officer/onbehalf/?$",
        officer.TablesOfficerOnBehalfView.as_view(),
        name="tables_officer_onbehalf",
    ),
    re_path(
        r"^dashboard/data/applications/officer/onbehalf/?$",
        officer.DataTableApplicationsOfficerOnBehalfView.as_view(),
        name="data_application_officer_onbehalf",
    ),
    re_path(
        r"^dashboard/data/applications/customer/?$",
        customer.DataTableApplicationCustomerView.as_view(),
        name="data_application_customer",
    ),
    re_path(
        r"^dashboard/data/applications/assessor/?$",
        assessor.DataTableApplicationAssessorView.as_view(),
        name="data_application_assessor",
    ),
    # Licences
    re_path(
        r"^dashboard/tables/licences/officer/?$",
        officer.TablesLicencesOfficerView.as_view(),
        name="tables_licences_officer",
    ),
    re_path(
        r"^dashboard/data/licences/officer/?$",
        officer.DataTableLicencesOfficerView.as_view(),
        name="data_licences_officer",
    ),
    re_path(
        r"^dashboard/data/licences/customer/?$",
        customer.DataTableLicencesCustomerView.as_view(),
        name="data_licences_customer",
    ),
    re_path(
        r"^dashboard/bulk-licence-renewal-pdf/?$",
        officer.BulkLicenceRenewalPDFView.as_view(),
        name="bulk_licence_renewal_pdf",
    ),
    # Returns
    re_path(
        r"^dashboard/tables/returns/officer/?$",
        officer.TablesReturnsOfficerView.as_view(),
        name="tables_returns_officer",
    ),
    re_path(
        r"^dashboard/data/returns/officer/?$",
        officer.DataTableReturnsOfficerView.as_view(),
        name="data_returns_officer",
    ),
    re_path(
        r"^dashboard/data/returns/officer/onbehalf/?$",
        officer.DataTableReturnsOfficerOnBehalfView.as_view(),
        name="data_returns_officer_onbehalf",
    ),
    re_path(
        r"^dashboard/data/returns/customer/?$",
        customer.DataTableReturnsCustomerView.as_view(),
        name="data_returns_customer",
    ),
]
