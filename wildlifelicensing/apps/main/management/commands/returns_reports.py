from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.core.mail.message import EmailMessage
from django.conf import settings
from wildlifelicensing.apps.returns.models import Return
import datetime
from zipfile import ZipFile
import os


class Command(BaseCommand):
    help = 'Run the Returns Report'

    def handle(self, *args, **options):
        dt = datetime.date(2018,1,1)

        filename1 = f'returns_report_reg17_{datetime.datetime.now().strftime("%Y%m%d")}.csv'
        with open(filename1, "w") as f:
            hdr = 'LODGEMENT_NUMBER|*|LICENCE REFERENCE|*|LODGEMENT_DATE|*|STATUS|*|RETURN_NAME|*|DATE|*|FATE|*|SITE|*|ZONE|*|COUNT|*|DATUM|*|METHOD|*|EASTING|*|MARKING|*|NAME_ID|*|SAMPLES|*|ACCURACY|*|LATITUDE|*|LOCATION|*|NORTHING|*|CERTAINTY|*|LONGITUDE|*|IDENTIFIER|*|COMMON_NAME|*|TRANSMITTER|*|VOUCHER_REF|*|SPECIES_NAME|*|SPECIES_GROUP\n'
            f.write(hdr)
            for ret in Return.objects.filter(returntable__name__in=['regulation-17'], lodgement_date__gt=dt):
                for return_table in ret.returntable_set.all():
                    for return_row in return_table.returnrow_set.all():
                        data = "|*|".join(str(val) for val in return_row.data.values())
                        line = f'{ret.lodgement_number}|*|{ret.licence.reference}|*|{ret.lodgement_date}|*|{ret.status}|*|{return_table.name}|*|{data}\n'
                        #print(ret.lodgement_number, ret.lodgement_date, ret.status, return_table.name, data)

                        f.write(line)


        filename2 = f'returns_report_reg15_{datetime.datetime.now().strftime("%Y%m%d")}.csv'
        with open(filename2, "w") as f:
            hdr = 'LODGEMENT_NUMBER|*|LICENCE REFERENCE|*|LODGEMENT_DATE|*|STATUS|*|RETURN_NAME|*|COMMENTS|*|NUMBER TAKEN|*|CONDITION WHEN CAPTURED|*|DATE COLLECTED/DESTROYED|*|DATE RELEASED|*|LOCATION RELEASED|*|SPECIES|*|LOCATION COLLECTED\n'
            f.write(hdr)
            for ret in Return.objects.filter(returntable__name__in=['regulation-15'], lodgement_date__gt=dt):
                for return_table in ret.returntable_set.all():
                    for return_row in return_table.returnrow_set.all():
                        data = "|*|".join(str(val) for val in return_row.data.values())
                        line = f'{ret.lodgement_number}|*|{ret.licence.reference}|*|{ret.lodgement_date}|*|{ret.status}|*|{return_table.name}|*|{data}\n'
                        #print(ret.lodgement_number, ret.lodgement_date, ret.status, return_table.name, data)

                        f.write(line)

        filename_zip = f'returns_reports_{datetime.datetime.now().strftime("%Y%m%d")}.zip'
        with ZipFile(filename_zip, 'w') as zipObj:
            # Add multiple files to the zip
            zipObj.write(filename1)
            zipObj.write(filename2)

        email = EmailMessage()
        email.subject = 'Wildlife Licensing Returns Report'
        email.body = 'Wildlife Licensing Returns Report'
        email.from_email = settings.EMAIL_FROM 
        email.to = settings.REPORTS_EMAIL if isinstance(settings.REPORTS_EMAIL, list) else [settings.REPORTS_EMAIL]
        email.attach_file(filename_zip)

        res = email.send()

        # cleanup
        os.remove(filename1)
        os.remove(filename2)
        os.remove(filename_zip)



