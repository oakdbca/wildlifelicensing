import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.generic import View

from wildlifelicensing.apps.main.models import NomosTaxonomy

logger = logging.getLogger(__name__)


class SpeciesNamesJSON(View):
    def get(self, request, *args, **kwargs):
        search = request.GET.get("search", None)
        if not search:
            return JsonResponse([], safe=False)

        names_qs = (
            NomosTaxonomy.objects
            .filter(name__icontains=search)
            .values_list("name", flat=True)
            .distinct()[:settings.NOMOS_MAXIMUM_SEARCH_RESULTS]
        )

        names = list(names_qs)
        return JsonResponse(names, safe=False)
