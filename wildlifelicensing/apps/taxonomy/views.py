import json
import logging

import requests
from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View

logger = logging.getLogger("log")

if settings.DEBUG:
    requests.packages.urllib3.disable_warnings()


def add_filter(cql_filter, params):
    if "cql_filter" not in params:
        params["cql_filter"] = cql_filter
    else:
        params["cql_filter"] = params["cql_filter"] + " AND " + cql_filter


class SpeciesNamesJSON(View):
    def get(self, request, *args, **kwargs):
        """
        Search herbie for species and return a list of matching species in the form 'scientific name (common name)'.
        The 'search' parameter is used to search (icontains like) through the species_name (scientific name)
        and vernacular property (common name).
        The 'type'=['fauna'|'flora'] parameter can be used to limit the kingdom.

        :return: a list of matching species in the form 'scientific name (common name)'
        """
        base_url = settings.HERBIE_SPECIES_WFS_URL
        params = {"propertyName": "(species_name,vernacular)", "sortBy": "species_name"}
        search = request.GET.get("search")
        if search:
            filter_ = "(species_name ILIKE '%{0}%' OR vernacular ILIKE '%{0}%')".format(
                search
            )
            add_filter(filter_, params)
        kingdom = request.GET.get("type")
        fauna_kingdom = 5
        if kingdom == "fauna":
            add_filter(f"kingdom_id IN ({fauna_kingdom})", params)
        elif kingdom == "flora":
            add_filter(f"kingdom_id NOT IN ({fauna_kingdom})", params)
        r = requests.get(base_url, params=params, verify=False)
        names = []
        try:
            features = r.json()["features"]
            for f in features:
                name = f["properties"]["species_name"]
                common_name = (
                    f["properties"]["vernacular"]
                    if "vernacular" in f["properties"]
                    else None
                )
                if common_name:
                    name += f" ({common_name})"
                names.append(name)
        except Exception as e:
            logger.warning(
                f"Herbie returned an error: {e}. \nURL: {r.url}. \nResponse: {r.content}"
            )
        return HttpResponse(json.dumps(names), content_type="application/json")
