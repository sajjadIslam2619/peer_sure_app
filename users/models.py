from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Organization(models.Model):
    name = models.CharField(max_length=200, unique=True, default='No Organization')

    def __str__(self):
        return self.name
    
def get_default_organization():
    return Organization.objects.get_or_create(name='No Organization')[0]

class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name="user_profile", on_delete=models.CASCADE)
    role = models.CharField(max_length=100, default='mentee', choices=(
        ('mentor', 'Mentor'),
        ('mentee', 'Mentee'),
    ))

    mentor_email = models.EmailField(blank=True)
    organizations = models.ManyToManyField(Organization, blank=True)

    def save(self, *args, **kwargs):
        # Add default organization if none is set
        super().save(*args, **kwargs)  # Save the user profile first to get an ID
        if not self.organizations.exists():
            self.organizations.add(get_default_organization())

    def __str__(self):
        return self.user.username
    
    
