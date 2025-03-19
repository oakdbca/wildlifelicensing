from django.urls import re_path

from wildlifelicensing.apps.returns.api import views

urlpatterns = [
    re_path(
        r"data/(?P<return_type_pk>[0-9]+)/(?P<resource_number>[0-9]+)/?",
        views.ReturnsDataView.as_view(),
        name="data",
    ),
    re_path(r"", views.ExplorerView.as_view(), name="explorer"),
]
