from django.contrib import admin
from django.contrib.auth.models import User, Group

# Although we already disabled /admin in urls.py,
# we unregister these just in case
admin.site.unregister(User)
admin.site.unregister(Group)
