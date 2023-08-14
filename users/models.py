from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name="user_profile", on_delete=models.CASCADE)
    role = models.CharField(max_length=100, default='mentee', choices=(
        ('mentor', 'Mentor'),
        ('mentee', 'Mentee'),
    ))

    mentor_email = models.EmailField(blank=True)

    def __str__(self):
        return self.user.username
    
    
