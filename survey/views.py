from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Survey, Question, Option, Response, UserComment
from .forms import SurveyForm
from django.views.decorators.csrf import csrf_exempt
from peer_sure_app.settings import CHECK_IN_SURVEY, PAST_HISTORY_SURVEY, DEMOGRAPHIC_SURVEY
from peer_sure_app.settings import (SURVEY_CATEGORY_CHECK_IN, SURVEY_CATEGORY_PMHx, SURVEY_CATEGORY_DEMOGRAPHY, 
                                    MESSAGE_SURVEY_CHECK_IN, MESSAGE_SURVEY_REQUIRED_SURVEY, MESSAGE_SURVEY_PENDING_SURVEY)
from django.contrib import messages
from users.models import Organization
import logging
logger = logging.getLogger(__name__)

PROFILE_SURVEY_TITLES = [PAST_HISTORY_SURVEY, DEMOGRAPHIC_SURVEY]

@csrf_exempt
@login_required
def survey_home(request):
    selected_organization = None
    if not request.user.is_superuser:
        selected_org_id = request.session.get('selected_organization_id')
        if selected_org_id:
            try:
                selected_organization = Organization.objects.get(id=selected_org_id)
                logger.info(f'Selected Organization :: {selected_organization}')
            except Organization.DoesNotExist:
                # Handle the case where the selected organization is not found
                return redirect('organization_selection')
        else:
            user_profile = request.user.user_profile
            organizations = user_profile.organizations.all()

            if organizations.exists():
                # User should have only one organization in this case. 
                # Otherwise app will redirect to organization selection view in the previous view.
                selected_organization = organizations.first()
                logger.info(f'Selected first organization: {selected_organization}')

                if selected_organization == 'No Organization':
                    logger.info('User has no organizations.')
                    messages.info(request, MESSAGE_SURVEY_CHECK_IN)
                    return redirect('profile')  # Redirect to profile section if 'No Organization' is selected

                # Store the selected organization in the session
                #request.session['selected_organization_id'] = selected_organization.id
            else:
                # Handle the case where the user has no organizations
                logger.info('User has no organizations.')
                messages.info(request, MESSAGE_SURVEY_CHECK_IN)
                return redirect('profile')  # Redirect to profile section if 'No Organization' is selected
    
        #surveys = Survey.objects.filter(organization=selected_organization, category__category=SURVEY_CATEGORY_CHECK_IN)
        try:
            # There should have only one Check-In survey for each Organization
            survey = Survey.objects.filter(organization=selected_organization, category__category=SURVEY_CATEGORY_CHECK_IN).first()
            if not survey:
                raise Survey.DoesNotExist
            logger.debug(f'Survey found: {survey.title} for organization {survey.organization}')
        except Survey.DoesNotExist:
            logger.error(f"Survey not available, required survey category: {SURVEY_CATEGORY_CHECK_IN}")
            return render(request, 'survey/error.html', {'message': f'{MESSAGE_SURVEY_REQUIRED_SURVEY} {SURVEY_CATEGORY_CHECK_IN}'})
        
    else:
        #surveys = Survey.objects.all()
        try:
            survey = Survey.objects.filter(category__category=SURVEY_CATEGORY_CHECK_IN).first()
            if not survey:
                raise Survey.DoesNotExist
            logger.debug(f'Survey found: {survey.title} for organization {survey.organization}')
        except Survey.DoesNotExist:
            logger.error(f"Survey not available, required survey category: {SURVEY_CATEGORY_CHECK_IN}")
            return render(request, 'survey/error.html', {'message': f'{MESSAGE_SURVEY_REQUIRED_SURVEY} {SURVEY_CATEGORY_CHECK_IN}'})
    
    '''
    survey = None

    for survey_obj in surveys:
        if str(survey_obj.category).strip().lower() == SURVEY_CATEGORY_CHECK_IN.strip().lower():
            logger.debug(f'Survey Category:  {survey_obj.category}')
            logger.debug(f'Survey Title:  {survey_obj.title}')
            survey = survey_obj
            break

    if survey is None:
        logger.debug(f'Survey not available, required survey category: {SURVEY_CATEGORY_CHECK_IN}')
        return render(request, 'survey/error.html', {'message': f'Survey not available, required survey category: {SURVEY_CATEGORY_CHECK_IN}'})
    '''
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
    PMH_survey_responses_exist = Response.objects.filter(
        user=user, 
        survey__category__category=SURVEY_CATEGORY_PMHx,
        survey__organization=selected_organization
    ).exists()
    demographic_responses_exist = Response.objects.filter(
        user=user, 
        survey__category__category=SURVEY_CATEGORY_DEMOGRAPHY,
    ).exists()

    pending_surveys = []

    if not PMH_survey_responses_exist:
        pending_surveys.append(SURVEY_CATEGORY_PMHx)

    if not demographic_responses_exist:
        pending_surveys.append(SURVEY_CATEGORY_DEMOGRAPHY)
    
    if pending_surveys:
        pending_surveys_str = ', '.join(pending_surveys)
        messages.info(request, f'{MESSAGE_SURVEY_PENDING_SURVEY} {pending_surveys_str}')

    return render(request, 'survey/survey.html', {'survey': survey, 'form': form})

def thank_you_view(request):
    return render(request, 'survey/thank_you.html')
