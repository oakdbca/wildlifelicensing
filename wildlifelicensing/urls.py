from django.conf import settings
from django.conf.urls import include, static, url
from django.contrib.auth import views as auth_views

from wildlifelicensing.admin import wildlife_licensing_admin_site
from wildlifelicensing.apps.dashboard.views.base import DashBoardRoutingView
from wildlifelicensing.apps.main import views

urlpatterns = [
    url(r"^$", DashBoardRoutingView.as_view(), name="home"),
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
    url(
        r"^private-media/view/(?P<file_id>\d+)-(\w+).(?P<extension>\w\w\w)$",
        views.getAppFile,
        name="view_private_file",
    ),
    url(
        r"^private-media/view/(?P<file_id>\d+)-(\w+).(?P<extension>\w\w\w\w)$",
        views.getAppFile,
        name="view_private_file2",
    ),
    url(r"^admin/", wildlife_licensing_admin_site.urls),
]

if settings.DEBUG:
    urlpatterns += static.static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# DBCA Template URLs
urlpatterns.append(
    url("logout/", auth_views.LogoutView.as_view(), {"next_page": "/"}, name="logout")
)
# if settings.ENABLE_DJANGO_LOGIN:
#     urlpatterns.append(
#         url(r"^ssologin/", auth_views.LoginView.as_view(), name="ssologin")
#     )
