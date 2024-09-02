from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth.models import User
from users.models import Organization

def get_default_organization_id():
    return Organization.objects.get_or_create(name='No Organization')[0].id

def get_default_survey_category_id():
    # Fetch or create the default 'No Category'
    return SurveyCategory.objects.get_or_create(category='No Category')[0].id

class SurveyCategory(models.Model):
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.category

class Survey(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.SET_DEFAULT, 
        default=get_default_organization_id
    )
    category = models.ForeignKey(
        SurveyCategory, 
        on_delete=models.SET_DEFAULT, 
        default=get_default_survey_category_id  # Creates one-to-many relationship
    )

    def __str__(self):
        return self.title

class Question(models.Model):
    ORIENTATION_CHOICES = (
        (-1, 'Negative'),
        (0, 'Neutral'),
        (1, 'Positive'),
    )
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    question = models.CharField(max_length=300)
    options = models.ManyToManyField('Option')
    categories = models.ManyToManyField('QuestionCategory', blank=True)
    weight = models.IntegerField(default=1)
    orientation = models.IntegerField(default=0, choices=ORIENTATION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.question
    
class QuestionCategory(models.Model):
    category = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.category

class Option(models.Model):
    option = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.option

class Response(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_options = models.CharField(max_length=100)
    date_responsed = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.survey.title} - {self.question.question}"
    
class UserComment(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    date_commented = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        #return f"Comment on {self.survey.title} by {self.user.username}"
        return self.user.username + '-' + str(self.comment[:20])
