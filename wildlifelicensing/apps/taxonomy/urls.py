from django.urls import re_path

from .views import SpeciesNamesJSON

urlpatterns = [
    re_path(r"species_name", SpeciesNamesJSON.as_view(), name="species_names_json"),
]
