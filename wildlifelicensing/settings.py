import logging
import os

import confy
from decouple import Csv, config

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("BASE_DIR", BASE_DIR)

if os.path.exists(BASE_DIR + "/.env"):
    confy.read_environment_file(BASE_DIR + "/.env")

from ledger_api_client.settings_base import *  # noqa: F403, E402

DEPT_DOMAINS = config(
    "DEPT_DOMAINS", default="dpaw.wa.gov.au,dbca.wa.gov.au", cast=Csv()
)
SYSTEM_MAINTENANCE_WARNING = config(
    "SYSTEM_MAINTENANCE_WARNING", default=24, cast=int
)  # hours
DEPRECATED = config("DEPRECATED", default=False, cast=bool)  # hours
REPORTS_EMAIL = config("REPORTS_EMAIL", default=ADMINS[0])

ROOT_URLCONF = "wildlifelicensing.urls"
SITE_ID = 1
INSTALLED_APPS += [
    "bootstrap3",
    "webtemplate_dbca",
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
    "wildlifelicensing.apps.taxonomy",
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
    "wildlifelicensing.apps.main.cron.FetchNomosFaunaCronJob",
    "appmonitor_client.cron.CronJobAppMonitorClient",
]

PAYMENT_SYSTEM_ID = config("PAYMENT_SYSTEM_ID", default="S369")
if not VALID_SYSTEMS:
    VALID_SYSTEMS = [PAYMENT_SYSTEM_ID]
SENIOR_VOUCHER_CODE = config("WL_SENIOR_VOUCHER_CODE", default="WL_SENIOR_VOUCHER")

PAYMENT_SYSTEM_PREFIX = config(
    "PAYMENT_SYSTEM_PREFIX", PAYMENT_SYSTEM_ID.replace("S", "0")
)  # '369'

SESSION_COOKIE_SECURE = config("SESSION_COOKIE_SECURE", True, cast=bool)
CSRF_COOKIE_SECURE = config("CSRF_COOKIE_SECURE", True, cast=bool)
SESSION_COOKIE_AGE = config("SESSION_COOKIE_AGE", 3600, cast=int)  # 1 hour

DEFAULT_HOST = "https://wildlifelicensing.dbca.wa.gov.au"
if EMAIL_INSTANCE.lower() == "dev":
    DEFAULT_HOST = "https://wildlifelicensing-dev.dbca.wa.gov.au"
if EMAIL_INSTANCE.lower() == "uat":
    DEFAULT_HOST = "https://wildlifelicensing-uat.dbca.wa.gov.au"
#
NOTIFICATION_HOST = config(
    "NOTIFICATION_HOST",
    default=DEFAULT_HOST,
)

# set data_upload_max params, otherwise use django default values
DATA_UPLOAD_MAX_NUMBER_FIELDS = config(
    "DATA_UPLOAD_MAX_NUMBER_FIELDS", default=250000, cast=int
)
DATA_UPLOAD_MAX_MEMORY_SIZE = config(
    "DATA_UPLOAD_MAX_MEMORY_SIZE", default=10485760, cast=int
)  # 2.5 MB

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

CACHE_KEY_LEDGER_EMAIL_USER = "ledger-email-user-{}"

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
    "wildlifelicensing.middleware.FirstTimeNagScreenMiddleware",
    "wildlifelicensing.middleware.PaymentSessionMiddleware",
    "wildlifelicensing.middleware.RevisionOverrideMiddleware",
    "wildlifelicensing.middleware.CacheControlMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
]

MIDDLEWARE = MIDDLEWARE_CLASSES
MIDDLEWARE_CLASSES = None

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

SYSTEM_NAME = config("SYSTEM_NAME", default="Wildlife Licensing")
SYSTEM_NAME_SHORT = config("SYSTEM_NAME_SHORT", default="WLS")

SUPPORT_EMAIL = config(
    "SUPPORT_EMAIL", default="wildlifelicensing@dpaw.wa.gov.au"
).lower()

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

INTERNAL_GROUPS = [
    GROUP_NAME_OFFICERS,
    GROUP_NAME_ASSESSORS,
]


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

if DEBUG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": config("DJANGO_LOG_LEVEL", default="INFO"),
                "propagate": False,
            },
        },
    }

REST_FRAMEWORK = {
    "DATE_FORMAT": "%d/%m/%Y",
}

TEMPLATE_GROUP = config("TEMPLATE_GROUP", default="wildlife_licensing")
TEMPLATE_TITLE = config("TEMPLATE_TITLE", default="Wildlife Licensing")
LEDGER_TEMPLATE = "bootstrap5"

LEDGER_UI_ACCOUNTS_MANAGEMENT = [
    {"email": {"options": {"view": True, "edit": False}}},
    {"first_name": {"options": {"view": True, "edit": True}}},
    {"last_name": {"options": {"view": True, "edit": True}}},
    {"title": {"options": {"view": True, "edit": True}}},
    {"dob": {"options": {"view": True, "edit": True}}},
    {"phone_number": {"options": {"view": True, "edit": True}}},
    {"mobile_number": {"options": {"view": True, "edit": True}}},
    {"fax_number": {"options": {"view": True, "edit": True}}},
    {"identification": {"options": {"view": True, "edit": True}}},
]

LEDGER_UI_ACCOUNTS_MANAGEMENT_KEYS = []
for am in LEDGER_UI_ACCOUNTS_MANAGEMENT:
    LEDGER_UI_ACCOUNTS_MANAGEMENT_KEYS.append(list(am.keys())[0])

LEDGER_UI_URL = config("LEDGER_UI_URL", "")

TEMPLATES[0]["OPTIONS"]["context_processors"].append(
    "wildlifelicensing.context_processors.config"
)

LEDGER_DEFAULT_LINE_STATUS = config("LEDGER_DEFAULT_LINE_STATUS", default=1, cast=int)
DEFAULT_ORACLE_CODE = config(
    "DEFAULT_ORACLE_CODE", default="WILDLIFE_LICENSING_DEFAULT_ORACLE_CODE"
)
SENIOR_VOUCHER_ORACLE_CODE = config(
    "SENIOR_VOUCHER_ORACLE_CODE",
    default="WILDLIFE_LICENSING_SENIOR_VOUCHER_ORACLE_CODE",
)

DEFAULT_FORM_DATETIME_FORMAT = "%d/%m/%Y %H:%M:%S"
DEFAULT_FORM_DATE_FORMAT = "%d/%m/%Y"

CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())

NOMOS_BLOB_URL = config("NOMOS_BLOB_URL", default="")
NOMOS_KINGDOM_IDS_LIST = config(
    "NOMOS_KINGDOM_IDS_LIST", default="1,2,5,6", cast=Csv(int)
)
NOMOS_TAXONOMY_SEARCH_RESULTS_LIMIT = config(
    "NOMOS_TAXONOMY_SEARCH_RESULTS_LIMIT", default=20, cast=int
)
