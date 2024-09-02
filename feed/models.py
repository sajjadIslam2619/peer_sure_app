from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
from users.models import Organization

def get_no_organization_id():
    # Retrieves the "No Organization" object or creates it if it doesn't exist
    no_org, created = Organization.objects.get_or_create(name="No Organization")
    return no_org.id 

class Post(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    anonymous = models.BooleanField(default=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, default=get_no_organization_id)

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk})
    
class Comment(models.Model):
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    comment_post = models.ForeignKey(Post, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering=['-date_posted']

    def __str__(self):
        return str(self.author) + ' comment ' + str(self.content[:30])

    
