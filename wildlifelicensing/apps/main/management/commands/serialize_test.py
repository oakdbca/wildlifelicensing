from django.core.management.base import BaseCommand

from wildlifelicensing.apps.applications.models import Application
from wildlifelicensing.preserialize.serialize import serialize


class Command(BaseCommand):
    help = "serialize test"

    def handle(self, *args, **options):
        errors = []
        for idx, a in enumerate(Application.objects.all()):
            try:
                serialize(
                    a,
                    related={
                        "applicant": {
                            "exclude": [
                                "residential_address",
                                "postal_address",
                                "billing_address",
                            ]
                        },
                        "proxy_applicant": {
                            "exclude": [
                                "residential_address",
                                "postal_address",
                                "billing_address",
                            ]
                        },
                        "assigned_officer": {
                            "exclude": [
                                "residential_address",
                                "postal_address",
                                "billing_address",
                            ]
                        },
                        "applicant_profile": {
                            "fields": ["email", "id", "institution", "name"]
                        },
                        "previous_application": {
                            "exclude": [
                                "applicant",
                                "applicant_profile",
                                "previous_application",
                                "licence",
                            ]
                        },
                        "licence": {
                            "related": {
                                "holder": {
                                    "exclude": [
                                        "residential_address",
                                        "postal_address",
                                        "billing_address",
                                    ]
                                },
                                "issuer": {
                                    "exclude": [
                                        "residential_address",
                                        "postal_address",
                                        "billing_address",
                                    ]
                                },
                                "profile": {
                                    "related": {
                                        "user": {
                                            "exclude": [
                                                "residential_address",
                                                "postal_address",
                                                "billing_address",
                                            ]
                                        }
                                    },
                                    "exclude": ["postal_address"],
                                },
                            },
                            "exclude": [
                                "holder",
                                "issuer",
                                "profile",
                                "licence_ptr",
                                "replaced_by",
                            ],
                        },
                    },
                )

            except Exception as e:
                if "residential_address" in str(e) and str(e).split()[0] not in errors:
                    errors.append(str(e).split()[0])
                    print(idx, a.id, e, errors)
                    print

        print(f"Total Errors: {errors}")
        print
