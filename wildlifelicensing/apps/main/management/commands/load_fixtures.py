from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Load all the fixtures"

    fixtures = [
        "conditions",
        "groups",
        "licences",
        "default-conditions",
        "returns",
        "regions",
        "products",
    ]

    def handle(self, *args, **options):
        for fixture in self.fixtures:
            print(f"load {fixture}")
            call_command("loaddata", fixture)
