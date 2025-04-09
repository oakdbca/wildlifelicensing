from django.core.management.base import BaseCommand
from django.db import connection
from ledger_api_client.managed_models import SystemGroup, SystemGroupPermission


class Command(BaseCommand):
    help = "Creates system group permissions from old auth group permissions"

    def handle(self, *args, **options):
        assessors_added_count = 0
        officers_added_count = 0
        assessors_group = SystemGroup.objects.get_or_create(name="Assessors")
        officers_group = SystemGroup.objects.get_or_create(name="Officers")
        with connection.cursor() as cursor:
            try:
                cursor.execute(
                    """
                    SELECT *
                    FROM accounts_emailuser_groups
                    LEFT JOIN auth_group ON accounts_emailuser_groups.group_id=auth_group.id
                    WHERE auth_group.name = 'Assessors';
                    """
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        "Error fetching from accounts_emailuser_groups and/or auth_group table(s) "
                        "Please make sure the table(s) exist and try again: {}".format(
                            e
                        )
                    )
                )
                return
            for row in cursor.fetchall():
                columns = [col[0] for col in cursor.description]
                system_group_permission, created = (
                    SystemGroupPermission.objects.get_or_create(
                        system_group=assessors_group,
                        emailuser_id=row[columns.index("emailuser_id")],
                    )
                )
                if created:
                    assessors_added_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully created {} system group permissions for Assessors".format(
                        assessors_added_count
                    )
                )
            )

            try:
                cursor.execute(
                    """
                    SELECT *
                    FROM accounts_emailuser_groups
                    LEFT JOIN auth_group ON accounts_emailuser_groups.group_id=auth_group.id
                    WHERE auth_group.name = 'Officers';
                    """
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        "Error fetching from accounts_emailuser_groups and/or auth_group table(s) "
                        "Please make sure the table(s) exist and try again: {}".format(
                            e
                        )
                    )
                )
                return
            for row in cursor.fetchall():
                columns = [col[0] for col in cursor.description]
                system_group_permission, created = (
                    SystemGroupPermission.objects.get_or_create(
                        system_group=officers_group,
                        emailuser_id=row[columns.index("emailuser_id")],
                    )
                )
                if created:
                    officers_added_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    "Successfully created {} system group permissions for Officers".format(
                        officers_added_count
                    )
                )
            )
