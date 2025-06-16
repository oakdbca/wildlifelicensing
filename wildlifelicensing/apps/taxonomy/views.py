import logging

from django.http import JsonResponse
from django.views.generic import View

from wildlifelicensing.apps.main.models import NomosTaxonomy
from wildlifelicensing.apps.main.serializers import NomosTaxonomySerializer

logger = logging.getLogger(__name__)


class SpeciesNamesJSON(View):
    def get(self, request, *args, **kwargs):
        search = request.GET.get("search", None)
        if not search:
            return JsonResponse(
                [],
                content_type="application/json",
            )
        serializer = NomosTaxonomySerializer(
            NomosTaxonomy.objects.filter(name__icontains=search), many=True
        )
        return JsonResponse(serializer.data, safe=False)
