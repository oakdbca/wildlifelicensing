import logging
import os

from decouple import Csv, config

logger = logging.getLogger(__name__)


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("BASE_DIR", BASE_DIR)

from ledger_api_client.settings_base import *  # noqa: F403, E402

ROOT_URLCONF = "disturbance.urls"
SITE_ID = 1
DEPT_DOMAINS = config(
    "DEPT_DOMAINS", default="dpaw.wa.gov.au,dbca.wa.gov.au", cast=Csv()
)
SUPERVISOR_STOP_CMD = config("SUPERVISOR_STOP_CMD")
SYSTEM_MAINTENANCE_WARNING = config(
    "SYSTEM_MAINTENANCE_WARNING", default=24, cast=int
)  # hours
DEPRECATED = config("DEPRECATED", default=False, cast=bool)  # hours
REPORTS_EMAIL = config("REPORTS_EMAIL", default=ADMINS[0])

ROOT_URLCONF = "wildlifelicensing.urls"
SITE_ID = 1
INSTALLED_APPS += [
    "bootstrap3",
    "reversion",
    "ledger_api_client",
    "wildlifelicensing.apps.dashboard",
    "wildlifelicensing.apps.main",
    "wildlifelicensing.apps.applications",
    "wildlifelicensing.apps.emails",
    "wildlifelicensing.apps.returns",
    "wildlifelicensing.apps.customer_management",
    "wildlifelicensing.apps.reports",
    "wildlifelicensing.apps.payments",
    "appmonitor_client",
]

WSGI_APPLICATION = "wildlifelicensing.wsgi.application"

if DEPRECATED:
    # used to override payment_details.html template in ledger
    TEMPLATES[0]["DIRS"].insert(0, os.path.join(BASE_DIR, "templates"))
TEMPLATES[0]["DIRS"].append(os.path.join(BASE_DIR, "wildlifelicensing", "templates"))

del BOOTSTRAP3["css_url"]
# BOOTSTRAP3 = {
#    'jquery_url': '//static.dpaw.wa.gov.au/static/libs/jquery/2.2.1/jquery.min.js',
#    'base_url': '//static.dpaw.wa.gov.au/static/libs/twitter-bootstrap/3.3.6/',
#    'css_url': None,
#    'theme_url': None,
#    'javascript_url': None,
#    'javascript_in_head': False,
#    'include_jquery': False,
#    'required_css_class': 'required-form-field',
#    'success_css_class': '',
#    'set_placeholder': False,
# }

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles_wl")
STATICFILES_DIRS.append(
    os.path.join(os.path.join(BASE_DIR, "wildlifelicensing", "static"))
)

CRON_CLASSES = [
    # 'wildlifelicensing.apps.main.cron.CheckLicenceRenewalsCronJob',
    # 'wildlifelicensing.apps.returns.cron.CheckOverdueReturnsCronJob',
    "appmonitor_client.cron.CronJobAppMonitorClient",
]


HERBIE_SPECIES_WFS_URL = config(
    "HERBIE_SPECIES_WFS_URL",
    default="https://kmi.dpaw.wa.gov.au/geoserver/ows?service=wfs&version=1.1.0&"
    "request=GetFeature&typeNames=public:herbie_hbvspecies_public&outputFormat=application/json",
)

WL_PAYMENT_SYSTEM_ID = config("WL_PAYMENT_SYSTEM_ID", default="S369")
if not VALID_SYSTEMS:
    VALID_SYSTEMS = [WL_PAYMENT_SYSTEM_ID]
WL_SENIOR_VOUCHER_CODE = config("WL_SENIOR_VOUCHER_CODE", default="WL_SENIOR_VOUCHER")

# next setting is necessary to resolve absolute URL for the emails sent by the tasks running in cron.
DEFAULT_HOST = config(
    "DEFAULT_HOST", default="https://wildlifelicensing.dpaw.wa.gov.au"
)
# set data_upload_max params, otherwise use django default values
DATA_UPLOAD_MAX_NUMBER_FIELDS = config(
    "DATA_UPLOAD_MAX_NUMBER_FIELDS", default=1000, cast=int
)
DATA_UPLOAD_MAX_MEMORY_SIZE = config(
    "DATA_UPLOAD_MAX_MEMORY_SIZE", default=2621440, cast=int
)  # 2.5 MB
WL_PDF_URL = config("WL_PDF_URL", default="https://wildlifelicensing.dpaw.wa.gov.au")
INVOICE_UNPAID_WARNING = config(
    "INVOICE_UNPAID_WARNING",
    default="Your application cannot be processed until payment is received.",
)

SYSTEM_NAME = config("SYSTEM_NAME", default="Wildlife Licensing System")
EMAIL_FROM = config("EMAIL_FROM", default=ADMINS[0])
DEFAULT_FROM_EMAIL = EMAIL_FROM
TIME_ZONE = "Australia/Perth"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(BASE_DIR, "wildlifelicensing", "cache"),
    }
}

# Address settings
OSCAR_REQUIRED_ADDRESS_FIELDS = (
    "first_name",
    "last_name",
    "line1",
    "line4",
    "postcode",
    "country",
)

MIDDLEWARE_CLASSES += [
    "whitenoise.middleware.WhiteNoiseMiddleware",
]
MIDDLEWARE = MIDDLEWARE_CLASSES
MIDDLEWARE_CLASSES = None

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

SYSTEM_NAME = config("SYSTEM_NAME", default="Wildlife Licensing")
SYSTEM_NAME_SHORT = config("SYSTEM_NAME_SHORT", default="WLS")

SITE_PREFIX = config("SITE_PREFIX")
SITE_DOMAIN = config("SITE_DOMAIN")

SUPPORT_EMAIL = config(
    "SUPPORT_EMAIL", default="wildlifelicensing@" + SITE_DOMAIN
).lower()
DEP_URL = config("DEP_URL", default="www." + SITE_DOMAIN)
DEP_PHONE = config("DEP_PHONE", default="(08) 9219 9978")
DEP_PHONE_SUPPORT = config("DEP_PHONE_SUPPORT", default="(08) 9219 9000")
DEP_FAX = config("DEP_FAX", default="(08) 9423 8242")
DEP_POSTAL = config(
    "DEP_POSTAL",
    default="Locked Bag 104, Bentley Delivery Centre, Western Australia 6983",
)
DEP_NAME = config("DEP_NAME", default="Department of Parks and Wildlife")
DEP_NAME_SHORT = config("DEP_NAME_SHORT", default="DBCA")
DEP_POSTAL_ADDRESS_LINE_1 = config("DEP_POSTAL_ADDRESS_LINE_1", default="Locked Bag 30")
DEP_POSTAL_ADDRESS_LINE_2 = config(
    "DEP_POSTAL_ADDRESS_LINE_2", default="BENTLEY DELIVERY CENTRE"
)
DEP_STATE = config("DEP_STATE", default="WA")
DEP_POSTAL_POSTCODE = config("DEP_POSTAL_POSTCODE", default="6983")

BRANCH_NAME = config("BRANCH_NAME", default="Tourism and Concessions Branch")

GROUP_NAME_OFFICERS = "Officers"
GROUP_NAME_ASSESSORS = "Assessors"

# ---------- Cache keys ----------
CACHE_TIMEOUT_5_SECONDS = 5
CACHE_TIMEOUT_10_SECONDS = 10
CACHE_TIMEOUT_1_MINUTE = 60
CACHE_TIMEOUT_5_MINUTES = 60 * 5
CACHE_TIMEOUT_2_HOURS = 60 * 60 * 2
CACHE_TIMEOUT_24_HOURS = 60 * 60 * 24
CACHE_TIMEOUT_NEVER = None

CACHE_KEY_SUPERUSER_IDS = "superuser-ids"
CACHE_KEY_USER_BELONGS_TO_GROUP = "user-{user_id}-belongs-to-{group_name}"
