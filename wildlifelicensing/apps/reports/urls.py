from django.urls import re_path

from wildlifelicensing.apps.reports.views import (
    ApplicationsReportView,
    LicencesReportView,
    ReportsView,
    ReturnsReportView,
)

urlpatterns = [
    re_path("^$", ReportsView.as_view(), name="reports"),
    re_path(
        "applications_report/$",
        ApplicationsReportView.as_view(),
        name="applications_report",
    ),
    re_path("licences_report/$", LicencesReportView.as_view(), name="licences_report"),
    re_path("returns_report/$", ReturnsReportView.as_view(), name="returns_report"),
    # for payment reports see main.urls
]
