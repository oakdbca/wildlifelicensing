from django.urls import include
from django.urls import re_path as url

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
    url("^enter-return/([0-9]+)/$", EnterReturnView.as_view(), name="enter_return"),
    url("^curate-return/([0-9]+)/$", CurateReturnView.as_view(), name="curate_return"),
    url(
        "^view-return/([0-9]+)/$", ViewReturnReadonlyView.as_view(), name="view_return"
    ),
    url(
        "^download-template/([0-9]+)/?$",
        DownloadReturnTemplate.as_view(),
        name="download_return_template",
    ),
    url(
        "^amendment-request/$", AmendmentRequestView.as_view(), name="amendment_request"
    ),
    # communication log
    url(
        "^add-log-entry/([0-9]+)/$",
        AddReturnLogEntryView.as_view(),
        name="add_log_entry",
    ),
    url("^log-list/([0-9]+)/$", ReturnLogListView.as_view(), name="log_list"),
    # api
    url(r"^api/", include((api_urlpatterns, "api"), namespace="api")),
]
