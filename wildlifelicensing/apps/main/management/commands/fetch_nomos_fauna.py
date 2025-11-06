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

        try:
            NOMOS_KINGDON_IDS = {int(k) for k in settings.NOMOS_KINGDOM_IDS_LIST}
        except ValueError as e:
            logger.error(f"Invalid NOMOS kingdom IDs: {e}")
            return

        logger.info("NOMOS_KINGDON_IDS: %s", NOMOS_KINGDON_IDS)

        if not hasattr(settings, "NOMOS_BLOB_URL") or not settings.NOMOS_BLOB_URL:
            logger.error("NOMOS_BLOB_URL setting is not configured.")
            return

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
                response = requests.get(
                    url=settings.NOMOS_BLOB_URL, headers=headers, timeout=60
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                logger.error(f"Failed to connect to NOMOS BLOB URL: {e}")
                return

            logger.info("Done Fetching NOMOS data")
            try:
                taxon_json = response.json()
            except Exception as e:
                logger.error(f"Failed to decode JSON: {e}")
                return

            if test_mode:
                with open(local_file, "w", encoding="utf-8") as f:
                    json.dump(taxon_json, f, indent=2)
                logger.info("Test mode: Saved downloaded data to %s", local_file)

        count = 0
        for taxon in taxon_json:
            if taxon.get("kingdom_id") in NOMOS_KINGDON_IDS:
                vernaculars = taxon.get("vernaculars") or []
                vernacular_str = (
                    " (" + ", ".join(v.get("name", "") for v in vernaculars) + ")"
                    if vernaculars
                    else ""
                )
                fauna_taxon.append(
                    NomosTaxonomy(
                        name=taxon.get("canonical_name", "") + vernacular_str,
                        taxon_name_id=taxon.get("taxon_name_id"),
                    )
                )
                updates.append(taxon.get("taxon_name_id"))
                count += 1
                if count % 1000 == 0:
                    logger.info("%d Taxon Records fetched. Continuing...", count)

        logger.info("%d Taxon Records fetched in total.", count)

        try:
            # Use taxon_name_id as the unique key for de-duplication
            existing_ids = set(
                NomosTaxonomy.objects.values_list("taxon_name_id", flat=True)
            )

            # Create only those not already present
            new_fauna_taxon = [
                f for f in fauna_taxon if f.taxon_name_id not in existing_ids
            ]

            if new_fauna_taxon:
                NomosTaxonomy.objects.bulk_create(
                    new_fauna_taxon,
                    batch_size=5000,
                )

            # Optionally, update names for existing IDs if they have changed
            # Note: Django 1.11 has no bulk_update; perform targeted updates
            to_update = [
                f for f in fauna_taxon if f.taxon_name_id in existing_ids
            ]
            updates_performed = 0
            for f in to_update:
                # Update only when the stored name differs
                try:
                    obj = NomosTaxonomy.objects.get(taxon_name_id=f.taxon_name_id)
                    if obj.name != f.name:
                        obj.name = f.name
                        obj.save(update_fields=["name"])  # small, targeted update
                        updates_performed += 1
                except NomosTaxonomy.DoesNotExist:
                    # Shouldn't happen due to existing_ids check, but ignore safely
                    pass

            if updates_performed:
                logger.info("Updated %d existing taxonomy names.", updates_performed)
        except Exception as e:
            logger.error(f"Failed to save fauna taxonomy: {e}")
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
