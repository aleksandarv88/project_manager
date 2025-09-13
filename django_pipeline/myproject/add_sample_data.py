import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

import django
django.setup()

from hello.models import Item

# Add sample items
if not Item.objects.exists():
    Item.objects.create(name="Apple", description="A juicy fruit")
    Item.objects.create(name="Banana", description="A yellow fruit")
    print("Sample items added")
else:
    print("Items already exist")
