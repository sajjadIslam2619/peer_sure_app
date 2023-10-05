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


# Create your views here.
def vizual_home(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    selected_mentee_username = request.GET.get('mentee')

    print(f"Start Date: {start_date}, End Date: {end_date}")

    user = request.user
    mentor_email  = user.email

    mentee_list = UserProfile.objects.filter(mentor_email=mentor_email)

    all_mentees = []
    for mentee in mentee_list:
        mentee_obj= User.objects.get(username=mentee.user)
        all_mentees.append(mentee_obj.username)

    if selected_mentee_username is not None and selected_mentee_username != 'all':
        mentee_list = UserProfile.objects.filter(user__username=selected_mentee_username)
    
    if start_date:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            if end_date:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            else: 
                end_date_obj = datetime.today().date()
            responses = Response.objects.filter(date_responsed__range=(start_date_obj, end_date_obj)).all()
    else:
        responses = Response.objects.all()

    data_y = []
    
    for mentee in mentee_list:
        mentee_obj= User.objects.get(username=mentee.user)
        mentee_responses = responses.filter(user__username=mentee_obj.username)
        #mentee_responses.order_by('date_responsed')

        # Aggregate by day and sum the selected_options
        daily_sums = mentee_responses.annotate(
            int_selected_options=Cast('selected_options', IntegerField()),
            response_date=TruncDate('date_responsed')
        ).values('response_date').annotate(
            total_for_date=Sum('int_selected_options')
        ).order_by('response_date')

        print('daily_sums :: ', daily_sums)
        mentee_data_y = [entry['total_for_date'] for entry in daily_sums]
        data_y.append(mentee_data_y)

    if not data_y:
        df = pd.DataFrame({'X': [], 'Y': []})
    else:
        data_x = [f'Response/Week {i + 1}' for i in range(len(data_y[0]))]
        # Create a DataFrame for easier plotting.
        df = pd.DataFrame({'X': data_x})

        for idx, mentee_data in enumerate(data_y):
            mentee_name = mentee_list[idx].user  # Retrieve the mentee name
            df[f"{mentee_name}"] = mentee_data

    # Create a line chart.
    fig = px.line(df, x='X', y=df.columns[1:], title='Mentee Weekly Progress')

    # Converting the figure to HTML.
    graph_html = pio.to_html(fig, full_html=False)

    context = {
        'graph': graph_html,
        'all_mentees': all_mentees
    }

    return render(request, 'vizual/vizual.html', context)