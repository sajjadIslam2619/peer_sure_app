from django.shortcuts import render
from survey.models import Response
from django.contrib.auth.models import User
import plotly.express as px
import plotly.io as pio
from users.models import UserProfile
from survey.models import Question, Survey, Option, Response
from django.db.models import Sum, IntegerField
from django.db.models.functions import Cast, TruncDate
import pandas as pd
from datetime import datetime
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.db.models.functions import ExtractWeek, ExtractYear
import numpy as np
from peer_sure_app.settings import CHECK_IN_SURVEY, PAST_HISTORY_SURVEY

@csrf_exempt
@login_required
def vizual_home(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    selected_mentee_username = request.GET.get('mentee')
    
    context = {}
    context['selected_start_date'] = start_date
    context['selected_end_date'] = end_date
    context['selected_mentee_username'] = selected_mentee_username


    print(f"REQUESTED Start Date: {start_date}, End Date: {end_date}")

    user = request.user
    mentor_email  = user.email

    mentee_list = UserProfile.objects.filter(mentor_email=mentor_email)

    all_mentees = []
    for mentee in mentee_list:
        mentee_obj= User.objects.get(username=mentee.user)
        #all_mentees.append(mentee_obj.username)

    if selected_mentee_username is not None and selected_mentee_username != 'all':
        mentee_list = UserProfile.objects.filter(user__username=selected_mentee_username)
    
    if start_date: 
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        else: 
            end_date_obj = datetime.today().date()

        year_start, week_number_start, weekday_start = start_date_obj.isocalendar()
        year_end, week_number_end, weekday_end = end_date_obj.isocalendar()

    else:
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
            date_obj = datetime.today().date()
            year_start, week_number_start, weekday_start = date_obj.isocalendar()
            year_end, week_number_end, weekday_end = date_obj.isocalendar()
    
    print('START TIME: ', year_start, week_number_start, weekday_start)
    print('END TIME: ', year_end, week_number_end, weekday_end) 

    ## To retrieve the number of questions in a specific survey
    survey = Survey.objects.get(title=CHECK_IN_SURVEY)
    number_of_questions = Question.objects.filter(survey=survey).count()

    mentee_scores = {}

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
        weekly_response_count = {}

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
            weekly_response_count[(year, week_number)] = weekly_response_count.get((year, week_number), 0) + 1

        scores_list = []
        prev_score = 0
        
        for week in range(week_number_start, week_number_end + 1):
            if (year_start, week) in weekly_scores:
                number_of_weekly_response = weekly_response_count[(year, week_number)]/number_of_questions
                scores_list.append(weekly_scores[(year_start, week)]/number_of_weekly_response) # average the score
                #prev_score = weekly_scores[(year_start, week)]
            else:
                #scores_list.append(prev_score)
                scores_list.append(0)
        

        # Add the scores list to the mentee_scores dictionary
        mentee_scores[mentee_obj.username] = scores_list
    
    for mentee, scores in mentee_scores.items():
        print(f"{mentee}: {scores}")

    if not mentee_scores:
        df = pd.DataFrame({'Responses': [], 'Y': []})
    else:
        first_mentee = next(iter(mentee_scores.values()))
        #data_x = [f'Response/Week {i + 1}' for i in range(len(first_mentee))]
        data_x = [f'{year_start}-{week}' for week in range(week_number_start, week_number_end + 1)]

        df = pd.DataFrame({'Responses': data_x})
        for mentee_name, scores in mentee_scores.items():
            df[f"{mentee_name}"] = scores

    fig = px.line(df, x='Responses', y=df.columns[1:], title='Mentee Weekly Progress', labels={'value': 'Risk Score'})

    graph_html = pio.to_html(fig, full_html=False)

    context['graph'] = graph_html
    context['all_mentees'] = list(mentee_scores.keys())
    '''
    context = {
        'graph': graph_html,
        'all_mentees': list(mentee_scores.keys())  # List of mentee usernames
    }'''

    return render(request, 'vizual/vizual.html', context)