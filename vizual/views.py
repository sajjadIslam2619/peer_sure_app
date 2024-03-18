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
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404, render
from django.http import Http404
import plotly.graph_objects as go
from statistics import median
from django.contrib import messages
import logging
import os
logger = logging.getLogger(__name__)


@csrf_exempt
@login_required
def vizual_home(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    selected_mentee_username = request.GET.get('mentee')
    selected_question_id = request.GET.get('question')

    if selected_question_id is None or selected_question_id.lower() == 'none':
        question_filter = False
    else:
        question_filter = True

    try:
        check_in_survey = get_object_or_404(Survey, title=CHECK_IN_SURVEY)
    except Http404:
        return render(request, 'vizual/error.html', {'message': f'Survey not available, required survey: {CHECK_IN_SURVEY}'})
    
    all_questions = Question.objects.filter(survey=check_in_survey)
    question_map = {question.id: question.question for question in all_questions}

    context = {}
    context['selected_start_date'] = start_date
    context['selected_end_date'] = end_date
    context['selected_mentee_username'] = selected_mentee_username
    context['all_questions'] = all_questions
    context['selected_question'] = selected_question_id

    question_titles = {str(question.id): question.question for question in all_questions}
    context['question_titles'] = question_titles 

    logger.debug(f"REQUESTED Start Date: {start_date}, End Date: {end_date}")

    user = request.user
    mentor_email  = user.email

    mentee_list = UserProfile.objects.filter(mentor_email=mentor_email)

    all_mentees = []

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
        mentee_responses = Response.objects.filter(user__in=mentee_users, survey = check_in_survey)
        sorted_responses = mentee_responses.order_by('date_responsed')
        earliest_response = sorted_responses.first()

        if earliest_response:
            earliest_date_responsed = earliest_response.date_responsed
            start_date_obj = earliest_date_responsed
            year_start, week_number_start, weekday_start = earliest_date_responsed.date().isocalendar()
            if end_date:
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            else: 
                end_date_obj = datetime.today().date()
            year_end, week_number_end, weekday_end = end_date_obj.isocalendar()
        else:
            logger.debug(f'No responses found for mentees.')
            date_obj = datetime.today().date()
            start_date_obj = date_obj
            end_date_obj = date_obj
            year_start, week_number_start, weekday_start = date_obj.isocalendar()
            year_end, week_number_end, weekday_end = date_obj.isocalendar()
            messages.info(request, f'No responses found for mentees')

    
    logger.debug(f'START TIME: {year_start} {week_number_start} {weekday_start}')
    logger.debug(f'END TIME:  {year_end} {week_number_end} {weekday_end}')

    week_difference = (year_end - year_start) * 52 + (week_number_end - week_number_start) + 1
    
    number_of_questions = len(all_questions)
    #question_ids = set(Question.objects.filter(survey=check_in_survey).values_list('id', flat=True))
    if question_filter:
        if selected_question_id == 'all_questions':
            question_ids = set(question_map.keys())
        else:
            question_ids = {int(selected_question_id)}
    else: 
        question_ids = set()

    mentee_scores = {}
    mentee_scores_by_questions = {}
    mentee_stats = {}
    mentee_missing_responses_weeks = {}
    mentee_missing_responses_weeks_by_questions = {}
    mentee_missing_responses_weeks_by_question_id = {}
    mentee_color_map = {}
    colors = px.colors.qualitative.Set1

    if len(mentee_list) > len(colors):
        colors = colors * (len(mentee_list) // len(colors) + 1)

    for index, mentee in enumerate(mentee_list):
        mentee_obj= User.objects.get(username=mentee.user)
        logger.debug(f'Mentee Obj :: {mentee_obj}')
        mentee_color_map[mentee_obj.username] = colors[index]

        end_date_obj += timedelta(days=1)
        mentee_responses = Response.objects.filter( 
            user=mentee_obj,survey = check_in_survey,
            date_responsed__range=[start_date_obj, end_date_obj] ).order_by('date_responsed')

        weekly_scores = {}
        weekly_weighted_score_by_questions = {}
        weekly_scores_by_questions = {}
        weekly_response_count = {}
        weekly_response_count_by_questions = {}

        for response in mentee_responses:
            response_date = response.date_responsed
            selected_option = response.selected_options
            question_weight = response.question.weight
            question_orientation = response.question.orientation
            question_id = response.question.id
            question_str = response.question.question

            year, week_number, week_day = response_date.date().isocalendar()

            if selected_option.upper() in ["YES", "NO"]:
                is_yes = selected_option.upper() == "YES"
                option_type = "YES/NO"
                if question_orientation == 1:
                    score_original = int(is_yes)
                elif question_orientation == -1:
                    score_original = int(not is_yes)
                score_weighted = score_original * question_weight

            elif selected_option in ["1", "2", "3", "4", "5"]:
                option_type = "1-5"
                selected_option = int(selected_option)
                if question_orientation == -1:
                    selected_option = 6 - selected_option
                score_weighted = selected_option/5 * question_weight
                score_original = selected_option
            else:
                option_type = "Other"
                score_weighted = 0
                score_original = 0

            #weekly_scores[(year, week_number)] = weekly_scores.get((year, week_number), 0) + score_weighted
            weekly_weighted_score_by_questions[(year, week_number, question_id)] = weekly_weighted_score_by_questions.get((year, week_number, question_id), 0) + score_weighted
            weekly_scores_by_questions [(year, week_number, question_id)] = weekly_scores_by_questions.get((year, week_number, question_id), 0) + score_original
            weekly_response_count[(year, week_number)] = weekly_response_count.get((year, week_number), 0) + 1
            weekly_response_count_by_questions[(year, week_number, question_id)] = weekly_response_count_by_questions.get((year, week_number, question_id), 0) + 1

        # Iterate over weekly_scores_by_questions and aggregate scores by (year, week)
        for (year, week, question_id), score in weekly_weighted_score_by_questions.items():
            if (year, week) not in weekly_scores:
                weekly_scores[(year, week)] = 0
            total_response_by_questions = weekly_response_count_by_questions [year, week, question_id]
            weekly_scores[(year, week)] += score/total_response_by_questions # average calculate

        scores_list = []
        missing_week_list = []
        prev_score = 0

        week_itr = week_number_start
        year_itr = year_start
        
        #mentee_missing_responses_weeks_by_questions = {}
        for itr in range(week_difference):
            if week_itr > 52: 
                week_itr = 1
                year_itr = year_itr + 1
            
            if (year_itr, week_itr) in weekly_scores:
                #number_of_weekly_response = weekly_response_count[(year, week_number)]/number_of_questions
                #scores_list.append(weekly_scores[(year_itr, week_itr)]/number_of_weekly_response) # average the score
                scores_list.append(weekly_scores[(year_itr, week_itr)])
                #prev_score = weekly_scores[(year_itr, week_itr)]/number_of_weekly_response
                prev_score = weekly_scores[(year_itr, week_itr)]
            else:
                scores_list.append(prev_score)
                #scores_list.append(0)
                formatted_week = f'{week_itr:02d}'
                yr_wk = f'{year_itr}_{formatted_week}'
                yr_wk_missing_list = mentee_missing_responses_weeks.get(mentee_obj.username, [])
                yr_wk_missing_list.append(yr_wk)
                mentee_missing_responses_weeks[mentee_obj.username]= yr_wk_missing_list
                missing_week_list.append(f'{year_itr}_{week_itr}')
            
            # Append the aggregated score for the week, or 0 if there was no score that week
            #scores_list.append(weekly_scores.get((year_itr, week_itr), 0))
            week_itr = week_itr + 1
        
        all_scores_list_by_questions = {}
        for question_id in question_ids:
            scores_list_by_questions = []
            week_itr = week_number_start
            year_itr = year_start
            prev_score = 0
            for itr in range(week_difference):
                if week_itr > 52: 
                    week_itr = 1
                    year_itr = year_itr + 1

                if (year_itr, week_itr, question_id) in weekly_scores_by_questions:
                    number_of_weekly_response_by_question = weekly_response_count_by_questions[(year_itr, week_itr, question_id)]
                    scores_list_by_questions.append(weekly_scores_by_questions[(year_itr, week_itr, question_id)]/number_of_weekly_response_by_question) # average the score
                    prev_score = weekly_scores_by_questions[(year_itr, week_itr, question_id)]/number_of_weekly_response_by_question
                else:
                    #scores_list_by_questions.append(0)
                    scores_list_by_questions.append(prev_score)
                    formatted_week = f'{week_itr:02d}'
                    yr_wk = f'{year_itr}_{formatted_week}'
                    yr_wk_missing_set = set(mentee_missing_responses_weeks.get(mentee_obj.username, []))
                    yr_wk_missing_set.add(yr_wk)

                    mentee_missing_responses_weeks_by_questions = mentee_missing_responses_weeks_by_question_id.setdefault(question_id, {})
                    mentee_missing_responses_weeks_by_questions[mentee_obj.username] = yr_wk_missing_set

                week_itr = week_itr + 1


            all_scores_list_by_questions[question_id] = scores_list_by_questions
        
        # Add the scores list to the mentee_scores dictionary
        mentee_scores[mentee_obj.username] = scores_list
        mentee_scores_by_questions[mentee_obj.username] = all_scores_list_by_questions
        non_zero_scores = [score for score in scores_list if score > 0]
        mentee_median = median(non_zero_scores) if non_zero_scores else 0
        mentee_stats[mentee_obj.username] = {
                'median_score': round(mentee_median, 2),
                'zero_count': missing_week_list
            }
    
    for mentee, scores in mentee_scores.items():
        logger.debug(f"{mentee}: {scores}")

    df = pd.DataFrame()
    if not mentee_scores:
        df = pd.DataFrame({'Responses': [], 'Y': []})
        fig = go.Figure()
        fig.update_layout(title="No Data Available")
    else:
        data_x = []
        week_itr = week_number_start
        year_itr = year_start

        for itr in range(week_difference):
            if week_itr > 52: 
                week_itr = 1
                year_itr = year_itr + 1
            formatted_week = f'{week_itr:02d}'
            data_x.append(f'{year_itr}_{formatted_week}')
            week_itr = week_itr + 1
        
        df = pd.DataFrame({'Responses': data_x})

        for mentee_name, scores in mentee_scores.items():
            df[f"{mentee_name}"] = scores
        
        numeric_df = df.select_dtypes(include=[np.number])
        max_y_value = numeric_df.max().max() if not numeric_df.empty else 0
     
        #fig = px.line(df, x='Responses', y=df.columns[1:], labels={'value': 'Risk Score'})
        fig = go.Figure()
        
        for mentee_name, scores in mentee_scores.items():
            df[f"{mentee_name}"] = scores
            line_color = mentee_color_map.get(mentee_name, 'black')  # Default color if not found
            fig.add_scatter(x=df['Responses'], y=df[mentee_name], mode='lines', line=dict(color=line_color), name=mentee_name, showlegend=True)

        for mentee, weeks in mentee_missing_responses_weeks.items():
            if mentee in df.columns:
                marker_color = mentee_color_map.get(mentee, 'black')  # Use the same color map
                for week in weeks:
                    week_indices = df[df['Responses'] == week].index.tolist()
                    for idx in week_indices:
                        fig.add_scatter(x=[df['Responses'][idx]], 
                                        y=[df[mentee][idx]], 
                                        mode='markers+lines', 
                                        marker=dict(size=10, color=marker_color, symbol='x'),
                                        showlegend=False
                                        )
        fig.update_layout(yaxis=dict(range=[-1, max_y_value + 1]))

    # Convert the figure to HTML
    graph_html = pio.to_html(fig, full_html=False)
    
    df_by_questions = pd.DataFrame()
    all_graph_html_by_questions = {}
    if not mentee_scores_by_questions: 
        df_by_questions = pd.DataFrame({'Responses': [], 'Y': []})
    else:
         
        for question_id in question_ids:
            data_x = []
            week_itr = week_number_start
            year_itr = year_start

            for itr in range(week_difference):
                if week_itr > 52: 
                    week_itr = 1
                    year_itr = year_itr + 1
                formatted_week = f'{week_itr:02d}'
                data_x.append(f'{year_itr}_{formatted_week}')
                week_itr = week_itr + 1

            df_by_questions = pd.DataFrame({'Responses': data_x})
            for mentee, score_by_questions in mentee_scores_by_questions.items():

                if question_id in score_by_questions:
                    scores = score_by_questions[question_id]
                    # Ensure mentee_scores aligns with data_x in length
                    if len(scores) == len(data_x):
                        df_by_questions[mentee] = scores
                    else:
                        pass

            numeric_df = df_by_questions.select_dtypes(include=[np.number])
            max_y_value = numeric_df.max().max() if not numeric_df.empty else 0

            #fig_by_questions = px.line(df_by_questions, x='Responses', y=df_by_questions.columns[1:], labels={'value': 'Risk Score'})
            fig_by_questions = go.Figure()            

            for mentee in mentee_scores_by_questions.keys():
                line_color = mentee_color_map[mentee]
                fig_by_questions.add_scatter(
                    x=df_by_questions['Responses'], 
                    y=df_by_questions[mentee], 
                    mode='lines',
                    name=mentee,
                    line=dict(color=line_color),
                    showlegend=True
                )

                # Add markers for each specified week for the specific mentee for this question
                if question_id in mentee_missing_responses_weeks_by_question_id:
                    mentee_missing_weeks = mentee_missing_responses_weeks_by_question_id[question_id]
                    if mentee in mentee_missing_weeks:
                        weeks = mentee_missing_weeks[mentee]
                        for week in weeks:
                            week_indices = df_by_questions[df_by_questions['Responses'] == week].index.tolist()
                            for idx in week_indices:
                                fig_by_questions.add_scatter(
                                    x=[df_by_questions['Responses'][idx]], 
                                    y=[df_by_questions[mentee][idx]], 
                                    mode='markers+lines',  # Combine markers and lines
                                    marker=dict(color=line_color, size=10, symbol='x'),
                                    line=dict(color=line_color),
                                    showlegend=False  # Set to False to avoid duplicate legends
                                )
                if mentee_missing_responses_weeks_by_question_id:
                    fig_by_questions.update_layout(
                        annotations=[
                            go.layout.Annotation(
                                text="Marker 'x' indicates a missing response",
                                align='left',
                                showarrow=False,
                                xref='paper',
                                yref='paper',
                                x=0.5,
                                y=-0.25,
                                bordercolor='black',
                                borderwidth=1
                            )
                        ]
                    )
            fig_by_questions.update_layout(yaxis=dict(range=[-1, max_y_value + 1]))

            graph_html_by_questions = pio.to_html(fig_by_questions, full_html=False)
            all_graph_html_by_questions[question_id] = graph_html_by_questions

    context['mentee_stats'] = mentee_stats
    context['graph'] = graph_html
    context['graphs'] = all_graph_html_by_questions
    context['all_mentees'] = list(mentee_scores.keys())

    return render(request, 'vizual/vizual.html', context)