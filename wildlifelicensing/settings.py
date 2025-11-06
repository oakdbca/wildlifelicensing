from django.core.exceptions import ImproperlyConfigured

import os
import confy
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
confy.read_environment_file(BASE_DIR+"/.env")
os.environ.setdefault("BASE_DIR", BASE_DIR)

from ledger.settings_base import *
ROOT_URLCONF = 'disturbance.urls'
SITE_ID = 1
DEPT_DOMAINS = env('DEPT_DOMAINS', ['dpaw.wa.gov.au', 'dbca.wa.gov.au'])
SUPERVISOR_STOP_CMD = env('SUPERVISOR_STOP_CMD')
SYSTEM_MAINTENANCE_WARNING = env('SYSTEM_MAINTENANCE_WARNING', 24) # hours
DEPRECATED = env('DEPRECATED', False) # hours
REPORTS_EMAIL = env('REPORTS_EMAIL', 'jawaid.mushtaq@dbca.wa.gov.au')

ROOT_URLCONF = 'wildlifelicensing.urls'
SITE_ID = 1
INSTALLED_APPS += [
    'bootstrap3',
    'wildlifelicensing.apps.dashboard',
    'wildlifelicensing.apps.main',
    'wildlifelicensing.apps.applications',
    'wildlifelicensing.apps.emails',
    'wildlifelicensing.apps.returns',
    'wildlifelicensing.apps.customer_management',
    'wildlifelicensing.apps.reports',
    'wildlifelicensing.apps.payments',
    'appmonitor_client',
]

WSGI_APPLICATION = 'wildlifelicensing.wsgi.application'

if DEPRECATED:
    # used to override payment_details.html template in ledger
    TEMPLATES[0]['DIRS'].insert(0, os.path.join(BASE_DIR, 'templates'))
TEMPLATES[0]['DIRS'].append(os.path.join(BASE_DIR, 'wildlifelicensing', 'templates'))

if "css_url" in BOOTSTRAP3:
    del BOOTSTRAP3['css_url']

STATIC_ROOT=os.path.join(BASE_DIR, 'staticfiles_wl')
STATICFILES_DIRS.append(os.path.join(os.path.join(BASE_DIR, 'wildlifelicensing', 'static')))

CRON_CLASSES = [
    # 'wildlifelicensing.apps.main.cron.CheckLicenceRenewalsCronJob',
    # 'wildlifelicensing.apps.returns.cron.CheckOverdueReturnsCronJob',
    "wildlifelicensing.apps.main.cron.FetchNomosFaunaCronJob",
    "appmonitor_client.cron.CronJobAppMonitorClient",
]

WL_PAYMENT_SYSTEM_ID = env('WL_PAYMENT_SYSTEM_ID', 'S369')
if not VALID_SYSTEMS:
    VALID_SYSTEMS = [WL_PAYMENT_SYSTEM_ID]
WL_SENIOR_VOUCHER_CODE = env('WL_SENIOR_VOUCHER_CODE', 'WL_SENIOR_VOUCHER')

# next setting is necessary to resolve absolute URL for the emails sent by the tasks running in cron.
DEFAULT_HOST = env('DEFAULT_HOST', "https://wildlifelicensing.dpaw.wa.gov.au")
#set data_upload_max params, otherwise use django default values
DATA_UPLOAD_MAX_NUMBER_FIELDS = env('DATA_UPLOAD_MAX_NUMBER_FIELDS', 1000)
DATA_UPLOAD_MAX_MEMORY_SIZE = env('DATA_UPLOAD_MAX_MEMORY_SIZE', 2621440) #2.5 MB
WL_PDF_URL=env('WL_PDF_URL','https://wildlifelicensing.dpaw.wa.gov.au')
INVOICE_UNPAID_WARNING = env('INVOICE_UNPAID_WARNING', 'Your application cannot be processed until payment is received.')

SYSTEM_NAME = env('SYSTEM_NAME', 'Wildlife Licensing System')
EMAIL_FROM = env('EMAIL_FROM', ADMINS[0])
DEFAULT_FROM_EMAIL = EMAIL_FROM
TIME_ZONE = 'Australia/Perth'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': os.path.join(BASE_DIR, 'wildlifelicensing', 'cache'),
    }
}

NOMOS_BLOB_URL = env("NOMOS_BLOB_URL")
NOMOS_KINGDOM_IDS_LIST = env("NOMOS_KINGDOM_IDS_LIST", default=[1,2,5,6])
NOMOS_MAXIMUM_SEARCH_RESULTS = env("NOMOS_MAXIMUM_SEARCH_RESULTS", default=30)
NOMOS_FETCH_FAUNA_CRON_TIME_OF_DAY = env("NOMOS_FETCH_FAUNA_CRON_TIME_OF_DAY", default="00:00")