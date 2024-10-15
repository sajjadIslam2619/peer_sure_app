import csv
from django.http import HttpResponse
from django.contrib import admin
from .models import UserProfile, Organization

# Export Organization model data to CSV
def export_organizations_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="organizations.csv"'

    writer = csv.writer(response)
    # Write the header for Organization fields
    writer.writerow(['ID', 'Name'])

    # Write the data rows
    for organization in queryset:
        writer.writerow([organization.id, organization.name])

    return response

export_organizations_to_csv.short_description = 'Export selected Organizations to CSV'


# Export UserProfile model data to CSV
def export_user_profiles_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="user_profiles.csv"'

    writer = csv.writer(response)
    # Write the header for UserProfile fields
    writer.writerow(['ID', 'Username', 'Role', 'Mentor Email', 'Organizations'])

    # Write the data rows
    for user_profile in queryset:
        organizations = ", ".join([org.name for org in user_profile.organizations.all()])
        writer.writerow([
            user_profile.id, 
            user_profile.user.username, 
            user_profile.role, 
            user_profile.mentor_email, 
            organizations  # List of organization names
        ])

    return response

export_user_profiles_to_csv.short_description = 'Export selected User Profiles to CSV'


# Register the actions in the Admin interface
class UserProfileAdmin(admin.ModelAdmin):
    actions = [export_user_profiles_to_csv]

class OrganizationAdmin(admin.ModelAdmin):
    actions = [export_organizations_to_csv]

# Register the models and their respective admin classes
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Organization, OrganizationAdmin)
