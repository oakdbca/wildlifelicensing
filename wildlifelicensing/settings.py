import logging
import os

import confy
from confy import env

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.exists(BASE_DIR + "/.env"):
    confy.read_environment_file(BASE_DIR + "/.env")
os.environ.setdefault("BASE_DIR", BASE_DIR)

from ledger_api_client.settings_base import *  # noqa: F403

ROOT_URLCONF = "disturbance.urls"
SITE_ID = 1
DEPT_DOMAINS = env("DEPT_DOMAINS", ["dpaw.wa.gov.au", "dbca.wa.gov.au"])
SUPERVISOR_STOP_CMD = env("SUPERVISOR_STOP_CMD")
SYSTEM_MAINTENANCE_WARNING = env("SYSTEM_MAINTENANCE_WARNING", 24)  # hours
DEPRECATED = env("DEPRECATED", False)  # hours
REPORTS_EMAIL = env("REPORTS_EMAIL", "jawaid.mushtaq@dbca.wa.gov.au")

ROOT_URLCONF = "wildlifelicensing.urls"
SITE_ID = 1
INSTALLED_APPS += [
    "bootstrap3",
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

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles_wl")
STATICFILES_DIRS.append(
    os.path.join(os.path.join(BASE_DIR, "wildlifelicensing", "static"))
)

CRON_CLASSES = [
    "appmonitor_client.cron.CronJobAppMonitorClient",
]


HERBIE_SPECIES_WFS_URL = env(
    "HERBIE_SPECIES_WFS_URL",
    "https://kmi.dpaw.wa.gov.au/geoserver/ows?service=wfs&version=1.1.0&"
    "request=GetFeature&typeNames=public:herbie_hbvspecies_public&outputFormat=application/json",
)

WL_PAYMENT_SYSTEM_ID = env("WL_PAYMENT_SYSTEM_ID", "S369")
if not VALID_SYSTEMS:
    VALID_SYSTEMS = [WL_PAYMENT_SYSTEM_ID]
WL_SENIOR_VOUCHER_CODE = env("WL_SENIOR_VOUCHER_CODE", "WL_SENIOR_VOUCHER")

# next setting is necessary to resolve absolute URL for the emails sent by the tasks running in cron.
DEFAULT_HOST = env("DEFAULT_HOST", "https://wildlifelicensing.dpaw.wa.gov.au")
# set data_upload_max params, otherwise use django default values
DATA_UPLOAD_MAX_NUMBER_FIELDS = env("DATA_UPLOAD_MAX_NUMBER_FIELDS", 1000)
DATA_UPLOAD_MAX_MEMORY_SIZE = env("DATA_UPLOAD_MAX_MEMORY_SIZE", 2621440)  # 2.5 MB
WL_PDF_URL = env("WL_PDF_URL", "https://wildlifelicensing.dpaw.wa.gov.au")
INVOICE_UNPAID_WARNING = env(
    "INVOICE_UNPAID_WARNING",
    "Your application cannot be processed until payment is received.",
)

SYSTEM_NAME = env("SYSTEM_NAME", "Wildlife Licensing System")
EMAIL_FROM = env("EMAIL_FROM", ADMINS[0])
DEFAULT_FROM_EMAIL = EMAIL_FROM
TIME_ZONE = "Australia/Perth"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(BASE_DIR, "wildlifelicensing", "cache"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

PRIVATE_MEDIA_ROOT = os.path.join(BASE_DIR, "private-media")
PRIVATE_MEDIA_URL = "/private-media/"

MIDDLEWARE_CLASSES += [
    # "leaseslicensing.middleware.FirstTimeNagScreenMiddleware",
    # "leaseslicensing.middleware.CacheControlMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]
MIDDLEWARE = MIDDLEWARE_CLASSES
MIDDLEWARE_CLASSES = None

DEFAULT_CURRENCY = "AUD"
CURRENCY_FORMAT = {
    "AUD": {
        "currency_digits": False,
        "format_type": "accounting",
    },
}
