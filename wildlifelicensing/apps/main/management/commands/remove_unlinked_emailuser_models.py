from django.conf import settings
from django.core.management.base import BaseCommand
from ledger_api_client.ledger_models import EmailUserRO as EmailUser

from wildlifelicensing.apps.applications.models import Application
from wildlifelicensing.apps.main.models import WildlifeLicence


class Command(BaseCommand):
    help = (
        "Removes any models that are linked to email users that don't exist in the ledger database. "
        "This is required for testing the system in dev and uat since ledger dev and ledger uat do not "
        "have the same email users as ledger prod."
    )

    def handle(self, *args, **options):
        if (
            settings.EMAIL_INSTANCE.lower() == "prod"
            or settings.PRODUCTION_EMAIL is True
            or "prod" in settings.DATABASE_URL
        ):
            self.stdout.write(
                self.style.ERROR(
                    "This command should not be run on production. "
                    "Please run it on dev or uat only."
                )
            )
            return

        proceed = input(
            "Are you sure you want to delete the models linked to email users "
            "that don't exist in the ledger database? (y/n): "
        )

        if not proceed.lower() == "y":
            self.stdout.write(self.style.ERROR("Aborting..."))
            return

        application_ids_to_delete = []
        for a in Application.objects.all():
            if a.applicant_id:
                if not EmailUser.objects.filter(id=a.applicant_id).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Application {a.id} has an applicant that doesn't exist in the ledger database."
                        )
                    )
                    application_ids_to_delete.append(a.id)
                    continue

            if a.proxy_applicant_id:
                if not EmailUser.objects.filter(id=a.proxy_applicant_id).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Application {a.id} has a proxy applicant that doesn't exist in the ledger database."
                        )
                    )
                    application_ids_to_delete.append(a.id)
                    continue

            if a.assigned_officer_id:
                if not EmailUser.objects.filter(id=a.assigned_officer_id).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Application {a.id} has an assigned officer that doesn't exist in the ledger database."
                        )
                    )
                    application_ids_to_delete.append(a.id)

        if application_ids_to_delete:
            self.stdout.write(
                self.style.WARNING(
                    f"Deleting {len(application_ids_to_delete)} applications that "
                    "are linked to email users that don't exist in the ledger database."
                )
            )
            Application.objects.filter(id__in=application_ids_to_delete).delete()
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "No applications found that are linked to email users that "
                    "don't exist in the ledger database."
                )
            )

        licence_ids_to_delete = []
        for licence in WildlifeLicence.objects.all():
            if licence.profile.user_id:
                if not EmailUser.objects.filter(id=licence.profile.user_id).exists():
                    self.stdout.write(
                        self.style.WARNING(
                            f"Licence {licence.id} has an applicant that doesn't exist in the ledger database."
                        )
                    )
                    licence_ids_to_delete.append(licence.id)

        if licence_ids_to_delete:
            self.stdout.write(
                self.style.WARNING(
                    f"Deleting {len(licence_ids_to_delete)} licences that are linked to email users that "
                    "don't exist in the ledger database."
                )
            )
            WildlifeLicence.objects.filter(id__in=licence_ids_to_delete).delete()
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    "No licences found that are linked to email users that don't exist in the ledger database."
                )
            )
        self.stdout.write(self.style.SUCCESS("Done!"))
