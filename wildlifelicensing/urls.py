from django.conf import settings
from django.conf.urls import include, static
from django.contrib import admin
from django.urls import re_path as url
from ledger_api_client.urls import urlpatterns as ledger_patterns

from wildlifelicensing.apps.dashboard.views.base import DashBoardRoutingView

urlpatterns = [
    url(r"^ledger/admin/", admin.site.urls, name="ledger_admin"),
    url(r"^$", DashBoardRoutingView.as_view(), name="wl_home"),
    url(
        r"",
        include(("wildlifelicensing.apps.main.urls", "main"), namespace="wl_main"),
    ),
    url(
        r"",
        include(
            ("wildlifelicensing.apps.dashboard.urls", "dashboard"),
            namespace="wl_dashboard",
        ),
    ),
    url(
        r"^applications/",
        include(
            ("wildlifelicensing.apps.applications.urls", "applications"),
            namespace="wl_applications",
        ),
    ),
    url(
        r"^customer_management/",
        include(
            (
                "wildlifelicensing.apps.customer_management.urls",
                "customer_management",
            ),
            namespace="wl_customer_management",
        ),
    ),
    url(
        r"^reports/",
        include(
            ("wildlifelicensing.apps.reports.urls", "reports"), namespace="wl_reports"
        ),
    ),
    url(
        r"^returns/",
        include(
            ("wildlifelicensing.apps.returns.urls", "returns"), namespace="wl_returns"
        ),
    ),
    url(
        r"^payments/",
        include(
            ("wildlifelicensing.apps.payments.urls", "returns"), namespace="wl_payments"
        ),
    ),
] + ledger_patterns

if settings.DEBUG:
    urlpatterns += static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
