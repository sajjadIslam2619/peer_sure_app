# django models/objects are accessible from shell
# To run shell: python manage.py shell

import os
import django

# Set up the Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'peer_sure_app.settings')
django.setup()

from django.db.models import Sum, IntegerField
from django.db.models.functions import Cast, TruncDate
from feed.models import Post, Comment
from django.contrib.auth.models import User
from users.models import UserProfile
from survey.models import Question, Survey, Option, Response
from peer_sure_app.settings import CHECK_IN_SURVEY, PAST_HISTORY_SURVEY

# get all users/post
User.objects.all()
Post.objects.all()

# In application, get user from 'request' object. See feed/views.py for referance.
# Example Code to get user.
'''
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def my_view(request):
    # Access the logged-in user
    user = request.user

    # Now you can use the user object to access user properties
    username = user.username
    email = user.email
'''

# For DB query example, getting the first user or filttering any user. 
# create a post
user = User.objects.all().first()
post_13 = Post(title='post13', content='create post using model objects', author=user)
post_13.save()

post_14 = Post(title='post 14', content='testing python shell', author_id=user.id)
post_14.save()

# get first user
User.objects.first()

# filter user
User.objects.filter(username='mentee11')
User.objects.filter(username='mentee11').first() # if multiple user

# capture in a variable
user = User.objects.first()
user = User.objects.filter(username='mentee11')
user = User.objects.filter(username='mentee11').first()

# capture attribute, not working after filtering have to use first()
user.id
user.pk

user= User.objects.get(id=1)
user= User.objects.get(email='mentee11@mail.com')

post = Post.objects.first()
author_email = post.author.email

# get post written by a specific user
# modelname_set
user.post_set
user.post_set.all()

# create a post using the modelname_set, no need to set author and save
user.post_set.create(title='post 15', content='create post using modelname_set')


# check all attribute name
user.__dict__.keys()
#dict_keys(['_state', 'id', 'password', 'last_login', 'is_superuser', 'username', 'first_name', 'last_name', 'email', 'is_staff', 'is_active', 'date_joined'])
#dict_keys(['_state', 'id', 'user_id', 'role', 'mentor_email'])

# get posts's all comment and user
post = Post.objects.first()
comments = post.comment_set.all()

for comment in comments:
    content_text = comment.content
    author_name = comment.author.username  

    print(content_text)
    print(author_name)

# Find all mentee of a mentor
user_mentor = User.objects.filter(username='mentor1').first()
mentor_email  = user_mentor.email
mentee_list = UserProfile.objects.filter(mentor_email=mentor_email)

for mentee in mentee_list:
    print(mentee.user)
    mentee_obj= User.objects.get(username=mentee.user)
    print(mentee_obj.email)

# Find all survey-response and groupby 
responses = Response.objects.all()
mentee_responses = responses.filter(user__username='mentee11')
mentee_responses.order_by('date_responsed')

# Aggregate by day and sum the selected_options
daily_sums = mentee_responses.annotate(
    int_selected_options=Cast('selected_options', IntegerField()),
    response_date=TruncDate('date_responsed')
).values('response_date').annotate(
    total_for_date=Sum('int_selected_options')
).order_by('response_date')


surveys = Survey.objects.all()
for survey in surveys:
    #print("Survey Title:", survey.title)
    #print("Survey Description:", survey.description)
    if survey.title == CHECK_IN_SURVEY:
        print("Survey Title:", survey.title)
    print("-" * 50)


## To retrieve the number of questions in a specific survey titled 'Weekly Check In Survey' 
# Retrieve the Survey instance with the title 'Weekly Check In Survey'
survey = Survey.objects.get(title='Weekly Check In Survey')
# Count the number of questions related to this survey
number_of_questions = Question.objects.filter(survey=survey).count()
print(f"Number of questions in 'Weekly Check In Survey': {number_of_questions}")