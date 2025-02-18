#!/usr/bin/env python3
import os
import sys

# This import will automatically find the .env file and load the environment variables
from decouple import config  # noqa

if __name__ == "__main__":
    path = os.path.dirname(os.path.abspath(__file__))
    # Remove trailing slash
    if path.endswith("/"):
        path = path[:-1]
    project_folder_name = os.path.basename(path)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", f"{project_folder_name}.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
