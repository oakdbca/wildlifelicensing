from django.conf import settings
from django.conf.urls import include, static, url
from django.contrib import admin

from wildlifelicensing.apps.dashboard.views.base import DashBoardRoutingView

urlpatterns = [
    url(r"^ledger/admin/", admin.site.urls, name="ledger_admin"),
    url(r"^$", DashBoardRoutingView.as_view(), name="wl_home"),
    url(r"", include("wildlifelicensing.apps.main.urls", namespace="wl_main")),
    url(
        r"", include("wildlifelicensing.apps.dashboard.urls", namespace="wl_dashboard")
    ),
    url(
        r"^applications/",
        include(
            "wildlifelicensing.apps.applications.urls", namespace="wl_applications"
        ),
    ),
    url(
        r"^customer_management/",
        include(
            "wildlifelicensing.apps.customer_management.urls",
            namespace="wl_customer_management",
        ),
    ),
    url(
        r"^reports/",
        include("wildlifelicensing.apps.reports.urls", namespace="wl_reports"),
    ),
    url(
        r"^returns/",
        include("wildlifelicensing.apps.returns.urls", namespace="wl_returns"),
    ),
    url(
        r"^payments/",
        include("wildlifelicensing.apps.payments.urls", namespace="wl_payments"),
    ),
]

if settings.DEBUG:
    urlpatterns += static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
