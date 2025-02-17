from django.urls import include, re_path

from wildlifelicensing.apps.returns.api.urls import urlpatterns as api_urlpatterns
from wildlifelicensing.apps.returns.views import (
    AddReturnLogEntryView,
    AmendmentRequestView,
    CurateReturnView,
    DownloadReturnTemplate,
    EnterReturnView,
    ReturnLogListView,
    ViewReturnReadonlyView,
)

urlpatterns = [
    re_path("^enter-return/([0-9]+)/$", EnterReturnView.as_view(), name="enter_return"),
    re_path(
        "^curate-return/([0-9]+)/$", CurateReturnView.as_view(), name="curate_return"
    ),
    re_path(
        "^view-return/([0-9]+)/$", ViewReturnReadonlyView.as_view(), name="view_return"
    ),
    re_path(
        "^download-template/([0-9]+)/?$",
        DownloadReturnTemplate.as_view(),
        name="download_return_template",
    ),
    re_path(
        "^amendment-request/$", AmendmentRequestView.as_view(), name="amendment_request"
    ),
    # communication log
    re_path(
        "^add-log-entry/([0-9]+)/$",
        AddReturnLogEntryView.as_view(),
        name="add_log_entry",
    ),
    re_path("^log-list/([0-9]+)/$", ReturnLogListView.as_view(), name="log_list"),
    # api
    re_path(r"^api/", include((api_urlpatterns, "api"), namespace="api")),
]
