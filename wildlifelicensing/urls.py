from django import urls
from django.conf import settings
from django.conf.urls import include, static, url
from django.contrib import admin
from django.contrib.auth import views as auth_views

from wildlifelicensing.apps.dashboard.views.base import DashBoardRoutingView

urlpatterns = [
    urls.path(r"admin/", admin.site.urls),
    url(r"^$", DashBoardRoutingView.as_view(), name="wl_home"),
    url(
        r"",
        include(("wildlifelicensing.apps.main.urls", "wl_main"), namespace="wl_main"),
    ),
    url(
        r"",
        include(
            ("wildlifelicensing.apps.dashboard.urls", "wl_dashboard"),
            namespace="wl_dashboard",
        ),
    ),
    url(
        r"^applications/",
        include(
            ("wildlifelicensing.apps.applications.urls", "wl_applications"),
            namespace="wl_applications",
        ),
    ),
    url(
        r"^customer_management/",
        include(
            (
                "wildlifelicensing.apps.customer_management.urls",
                "wl_customer_management",
            ),
            namespace="wl_customer_management",
        ),
    ),
    url(
        r"^reports/",
        include(
            ("wildlifelicensing.apps.reports.urls", "wl_reports"),
            namespace="wl_reports",
        ),
    ),
    url(
        r"^returns/",
        include(
            ("wildlifelicensing.apps.returns.urls", "wl_returns"),
            namespace="wl_returns",
        ),
    ),
    url(
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
    urls.path(
        "logout/", auth_views.LogoutView.as_view(), {"next_page": "/"}, name="logout"
    )
)
if settings.ENABLE_DJANGO_LOGIN:
    urlpatterns.append(
        urls.re_path(r"^ssologin/", auth_views.LoginView.as_view(), name="ssologin")
    )
