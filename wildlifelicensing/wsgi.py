"""
WSGI config for ledger project.
It exposes the WSGI callable as a module-level variable named ``application``.
"""

import os

# This import will automatically find the .env file and load the environment variables
from decouple import config  # noqa
from django.core.wsgi import get_wsgi_application

path = os.path.dirname(os.path.abspath(__file__))
# Remove trailing slash
if path.endswith("/"):
    path = path[:-1]
project_folder_name = os.path.basename(path)

os.environ.setdefault(
    "BASE_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{project_folder_name}.settings")

application = get_wsgi_application()
