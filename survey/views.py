from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Survey, Question, Option, Response, UserComment
from .forms import SurveyForm
from django.views.decorators.csrf import csrf_exempt
from peer_sure_app.settings import CHECK_IN_SURVEY, PAST_HISTORY_SURVEY, DEMOGRAPHIC_SURVEY
from django.contrib import messages
import logging
logger = logging.getLogger(__name__)

PROFILE_SURVEY_TITLES = [PAST_HISTORY_SURVEY, DEMOGRAPHIC_SURVEY]

@csrf_exempt
@login_required
def survey_home(request):
    surveys = Survey.objects.all()
    survey = None
    
    for survey_obj in surveys:
        if survey_obj.title == CHECK_IN_SURVEY:
            logger.debug(f'Survey Title:  {survey_obj.title}')
            survey = survey_obj
            break

    if survey is None:
        logger.debug(f'Survey not available, required survey: {CHECK_IN_SURVEY}')
        return render(request, 'survey/error.html', {'message': f'Survey not available, required survey: {CHECK_IN_SURVEY}'})
    
    if request.method == 'POST':
        form = SurveyForm(request.POST, survey_id=survey.id)
        if form.is_valid():
            user = request.user  # Get the current authenticated user
            for question in Question.objects.filter(survey_id=survey.id):
                selected_option = form.cleaned_data[f'question_{question.id}']
                if selected_option:
                    selected_option_id = Option.objects.get(id=selected_option.id)
                    response = Response.objects.create(
                        survey=survey,
                        user=user,
                        question=question,
                        selected_options=selected_option_id.option  # Store the option's text, not the Option object
                    )
                    
            user_comments = form.cleaned_data.get('user_comments')
            if user_comments:
                UserComment.objects.create(
                    survey=survey,
                    user=request.user,
                    comment=user_comments
                )

            return redirect('thank_you')  # Redirect to a thank-you page after successful submission
    else:
        form = SurveyForm(survey_id=survey.id)
    
    user = request.user 
    PMH_survey_responses_exist = Response.objects.filter(user=user, survey__title=PAST_HISTORY_SURVEY).exists()
    demographic_responses_exist = Response.objects.filter(user=user, survey__title=DEMOGRAPHIC_SURVEY).exists()

    pending_surveys = []

    if not PMH_survey_responses_exist:
        pending_surveys.append(PAST_HISTORY_SURVEY)

    if not demographic_responses_exist:
        pending_surveys.append(DEMOGRAPHIC_SURVEY)
    
    if pending_surveys:
        pending_surveys_str = ', '.join(pending_surveys)
        messages.info(request, f'Please visit your profile to complete the pending surveys: {pending_surveys_str}')

    return render(request, 'survey/survey.html', {'survey': survey, 'form': form})

def thank_you_view(request):
    return render(request, 'survey/thank_you.html')
