import json
import logging
import os

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from wildlifelicensing.apps.main.models import NomosTaxonomy

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Fetch nomos data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--test",
            action="store_true",
            help="This flag makes testing much faster by saving the results nomos json to a file for reuse.",
        )

    def handle(self, *args, **options):
        logger.info("Running command %s", __name__)

        errors = []
        updates = []
        test_mode = options.get("test", False)
        fauna_taxon = []
        taxon_json = None
        local_file = "nomos_fauna.json"

        NOMOS_BLOB_URL = settings.NOMOS_BLOB_URL

        if not NOMOS_BLOB_URL:
            err_msg = "The NOMOS_BLOB_URL environment variable is not set."
            logger.error(err_msg)
            errors.append(err_msg)
            return

        NOMOS_KINGDOM_IDS = set(settings.NOMOS_KINGDOM_IDS_LIST)

        logger.info("NOMOS_KINGDOM_IDS: %s", NOMOS_KINGDOM_IDS)

        if test_mode and os.path.exists(local_file):
            logger.info("Test mode: Loading taxon data from %s", local_file)
            with open(local_file, encoding="utf-8") as f:
                taxon_json = json.load(f)
        else:
            logger.info("Requesting NOMOS BLOB URL")
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Accept-Encoding": "gzip, deflate",
            }
            try:
                response = requests.get(url=NOMOS_BLOB_URL, headers=headers, timeout=60)
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                err_msg = f"Failed to connect to NOMOS BLOB URL: {e}"
                logger.error(err_msg)
                errors.append(err_msg)
                return

            logger.info("Done Fetching NOMOS data")
            try:
                taxon_json = response.json()
            except Exception as e:
                err_msg = f"Failed to decode JSON: {e}"
                logger.error(err_msg)
                errors.append(err_msg)
                return

            if test_mode:
                with open(local_file, "w", encoding="utf-8") as f:
                    json.dump(taxon_json, f, indent=2)
                logger.info("Test mode: Saved downloaded data to %s", local_file)

        count = 0
        for taxon in taxon_json:
            if taxon.get("kingdom_id") in NOMOS_KINGDOM_IDS:
                vernaculars = taxon.get("vernaculars") or []
                vernacular_str = (
                    " (" + ", ".join(v.get("name", "") for v in vernaculars) + ")"
                    if vernaculars
                    else ""
                )
                fauna_taxon.append(
                    NomosTaxonomy(name=taxon.get("canonical_name", "") + vernacular_str)
                )
                updates.append(taxon.get("taxon_name_id"))
                count += 1
                if count % 1000 == 0:
                    logger.info("%d Taxon Records fetched. Continuing...", count)

        logger.info("%d Taxon Records fetched in total.", count)

        try:
            NomosTaxonomy.objects.bulk_create(
                fauna_taxon,
                ignore_conflicts=True,  # Ignore duplicate entries
                batch_size=5000,
            )
        except Exception as e:
            err_msg = f"Failed to save fauna taxonomy: {e}"
            logger.error(err_msg)
            errors.append(err_msg)
            return

        total = NomosTaxonomy.objects.count()
        updates_length = len(updates)
        fauna_taxon_length = len(fauna_taxon)
        logger.info(
            "Successfully attempted to bulk create %d NomosTaxonomy records. Table now contains %d records.",
            fauna_taxon_length,
            total,
        )
        if updates_length > total:
            logger.info(
                "%d records were ignored (most likely because they were duplicates).",
                updates_length - total,
            )

        cmd_name = __name__.split(".")[-1].replace("_", " ").upper()
        err_str = f"Errors: {len(errors)}" if errors else "Errors: 0"
        msg = f"Command {cmd_name} completed. {err_str}. JSON records processed: {len(updates)}."
        logger.info(msg)
