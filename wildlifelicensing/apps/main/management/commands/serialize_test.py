from django.core.management.base import BaseCommand
from django.core.management import call_command
from preserialize.serialize import serialize
from wildlifelicensing.apps.applications.models import Application


class Command(BaseCommand):
    help = 'serialize test'

    def handle(self, *args, **options):
        errors = []
        for idx, a in enumerate(Application.objects.all()):
            try:
                #k=serialize(a, exclude=['previous_application', 'licence', 'assigned_officer', 'applicant_profile', 'applicant'])
                k=serialize(a,
                    related={
                        'applicant': {'exclude': ['residential_address','postal_address','billing_address']},
                        'proxy_applicant': {'exclude': ['residential_address','postal_address','billing_address']},
                        'assigned_officer': {'exclude': ['residential_address','postal_address','billing_address']},
                        'applicant_profile':{'fields':['email','id','institution','name']},
                        'previous_application':{'exclude':['applicant','applicant_profile','previous_application','licence']},
                        'licence':{'related':{
                            'holder':{'exclude': ['residential_address','postal_address','billing_address']},
                            'issuer':{'exclude': ['residential_address','postal_address','billing_address']},
                            'profile':{'related': {'user': {'exclude': ['residential_address','postal_address','billing_address']}},
                                'exclude': ['postal_address']}
                        },'exclude':['holder','issuer','profile','licence_ptr', 'replaced_by']}
                    })


            except Exception, e:
                if 'residential_address' in str(e) and str(e).split()[0] not in errors:
                    errors.append(str(e).split()[0])
                    print idx, a.id, e, errors
                    print

        print 'Total Errors: {}'.format(errors)
        print
