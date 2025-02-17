from django.conf import settings
from django.conf.urls import include, static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, re_path

from wildlifelicensing.apps.dashboard.views.base import DashBoardRoutingView

urlpatterns = [
    path(r"admin/", admin.site.urls),
    re_path(r"^$", DashBoardRoutingView.as_view(), name="wl_home"),
    re_path(
        r"",
        include(("wildlifelicensing.apps.main.urls", "wl_main"), namespace="wl_main"),
    ),
    re_path(
        r"",
        include(
            ("wildlifelicensing.apps.dashboard.urls", "wl_dashboard"),
            namespace="wl_dashboard",
        ),
    ),
    re_path(
        r"^applications/",
        include(
            ("wildlifelicensing.apps.applications.urls", "wl_applications"),
            namespace="wl_applications",
        ),
    ),
    re_path(
        r"^customer_management/",
        include(
            (
                "wildlifelicensing.apps.customer_management.urls",
                "wl_customer_management",
            ),
            namespace="wl_customer_management",
        ),
    ),
    re_path(
        r"^reports/",
        include(
            ("wildlifelicensing.apps.reports.urls", "wl_reports"),
            namespace="wl_reports",
        ),
    ),
    re_path(
        r"^returns/",
        include(
            ("wildlifelicensing.apps.returns.urls", "wl_returns"),
            namespace="wl_returns",
        ),
    ),
    re_path(
        r"^payments/",
        include(
            ("wildlifelicensing.apps.payments.urls", "wl_payments"),
            namespace="wl_payments",
        ),
    ),
]

if settings.DEBUG:
    urlpatterns += static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# DBCA Template URLs
urlpatterns.append(
    path("logout/", auth_views.LogoutView.as_view(), {"next_page": "/"}, name="logout")
)
if settings.ENABLE_DJANGO_LOGIN:
    urlpatterns.append(
        re_path(r"^ssologin/", auth_views.LoginView.as_view(), name="ssologin")
    )
