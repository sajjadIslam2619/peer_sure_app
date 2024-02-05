import os
import django

# Set up the Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'peer_sure_app.settings')
django.setup()

from django.contrib.auth.models import User
from feed.models import Post, Comment
from users.models import UserProfile
from survey.models import Question, Survey, Option, Response
from users.models import UserProfile

from django.db.models import Sum, IntegerField
from django.db.models.functions import Cast, TruncDate
from django.db.models import Case, When, Value, IntegerField, FloatField, F
from django.db.models.functions import ExtractWeek, ExtractYear
from peer_sure_app.settings import CHECK_IN_SURVEY, PAST_HISTORY_SURVEY

import pandas as pd
from datetime import datetime

user_mentor = User.objects.filter(username='mentor3').first()
mentor_email  = user_mentor.email

start_date = '2023-10-13'
#start_date = None
#end_date = '2023-10-31'
end_date = ''


if start_date is None: 
    mentee_users = UserProfile.objects.filter(mentor_email=mentor_email).values_list('user', flat=True)
    mentee_responses = Response.objects.filter(user__in=mentee_users)
    sorted_responses = mentee_responses.order_by('date_responsed')
    earliest_response = sorted_responses.first()

    if earliest_response:
        earliest_date_responsed = earliest_response.date_responsed
        year_start, week_number_start, weekday_start = earliest_date_responsed.date().isocalendar()
        end_date_obj = datetime.today().date()
        year_end, week_number_end, weekday_end = end_date_obj.isocalendar()
    else:
        print(f"No responses found for user.")

else:
    if start_date:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        else: 
            end_date_obj = datetime.today().date()

        year_start, week_number_start, weekday_start = start_date_obj.isocalendar()
        year_end, week_number_end, weekday_end = end_date_obj.isocalendar()

print('START: ', year_start, week_number_start, weekday_start)
print('END: ', year_end, week_number_end, weekday_end) 

mentee_scores = {}
mentee_list = UserProfile.objects.filter(mentor_email=mentor_email)

for mentee in mentee_list:
    mentee_obj= User.objects.get(username=mentee.user)

    mentee_responses = Response.objects.filter(
        user=mentee_obj
    ).annotate(
        response_year=ExtractYear('date_responsed'),
        response_week=ExtractWeek('date_responsed')
    ).filter(
        response_year__gte=year_start,
        response_week__gte=week_number_start,
        response_year__lte=year_end,
        response_week__lte=week_number_end
    ).order_by('date_responsed')

    weekly_scores = {}

    for response in mentee_responses:
        response_date = response.date_responsed
        selected_option = response.selected_options
        question_weight = response.question.weight

        year, week_number, week_day = response_date.date().isocalendar()

        if selected_option.upper() in ["YES", "NO"]:
            option_type = "YES/NO"
            if selected_option.upper() == "YES":
                score = 1 * question_weight 
            else:
                score = 0
        elif selected_option in ["1", "2", "3", "4", "5"]:
            option_type = "1-5"
            score = int(selected_option)/5 * question_weight
        else:
            option_type = "Other"
            score = 0

        weekly_scores[(year, week_number)] = weekly_scores.get((year, week_number), 0) + score

        print(question_weight)
        print(selected_option)
        print(option_type)
        print(score)
        print('--------')
    '''
    scores_list = list(weekly_scores.values())
    mentee_scores[mentee_obj.username] = scores_list
    '''
    
    scores_list = []
    prev_score = 0
    for week in range(week_number_start, week_number_end + 1):
        if (year_start, week) in weekly_scores:
            scores_list.append(weekly_scores[(year_start, week)])
            prev_score = weekly_scores[(year_start, week)]
        else:
            scores_list.append(prev_score)

    # Add the scores list to the mentee_scores dictionary
    mentee_scores[mentee_obj.username] = scores_list
    
    print(mentee_obj)
    print(len(mentee_responses))
    print('==========')

for mentee, scores in mentee_scores.items():
    print(f"{mentee}: {scores}")



from django.db.models import Count
from django.utils import timezone


mentee_responses = Response.objects.filter(user__username='mentee43', survey__title = 'Weekly Check In Survey - 2')
sorted_responses = mentee_responses.order_by('date_responsed')
#grouped_responses = mentee_responses.values('date_responsed').annotate(count=Count('id'))
print('sorted_responses :: ', sorted_responses.count())
first_19_responses = sorted_responses[:19]
second_19_responses = sorted_responses[19:38]
date_string = '27-01-2024'
parsed_date = datetime.strptime(date_string, '%d-%m-%Y').date()
for response in second_19_responses:
    response.date_responsed = parsed_date
    response.save()

def main(): 
    print("hey there") 

# Using the special variable  
# __name__ 
if __name__=="__main__": 
    main()