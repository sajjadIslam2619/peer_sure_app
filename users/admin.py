from django.contrib import admin
from .models import UserProfile, Organization

# Register your models here.
admin.site.register(UserProfile)
admin.site.register(Organization)