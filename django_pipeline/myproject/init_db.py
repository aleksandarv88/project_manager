# Inside Python
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

import django
django.setup()

from django.core.management import call_command

call_command("makemigrations")
call_command("migrate")
