from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserProfileForm, HistorySurveyForm, DemographicSurveyForm
from django.views.decorators.csrf import csrf_exempt
from survey.models import Survey, Question, Option, Response
from peer_sure_app.settings import CHECK_IN_SURVEY, PAST_HISTORY_SURVEY, DEMOGRAPHIC_SURVEY
from django.shortcuts import get_object_or_404



#@csrf_exempt
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        profile_form = UserProfileForm(request.POST)
        if form.is_valid() and profile_form.is_valid():
            user = form.save()

            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()

            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('survey-home')
    else:
        form = UserRegisterForm()
        profile_form = UserProfileForm()
    return render(request, 'users/register.html', {'form': form, 'profile_form': profile_form})


#@csrf_exempt
@login_required
def profile(request):
    
    PMH_survey = get_object_or_404(Survey, title=PAST_HISTORY_SURVEY)

    if PMH_survey is None:
        return render(request, 'survey/error.html', {'message': 'No survey available.'})
    
    # Fetch existing responses for this user and survey
    existing_responses = Response.objects.filter(survey=PMH_survey, user=request.user)
    initial_data = {}
    if existing_responses.exists():
        for response in existing_responses:
            field_name = f'question_{response.question.id}'
            # Find the Option object that matches the response text
            try:
                selected_option = Option.objects.get(question=response.question, option=response.selected_options)
                initial_data[field_name] = selected_option.id
            except Option.DoesNotExist:
                # Handle the case where the option does not exist
                pass

    print('initial_data :: ', initial_data)
    
    if request.method == 'POST':
        #form = SurveyForm(request.POST, survey_id=survey_id)
        form = HistorySurveyForm(request.POST, survey_id=PMH_survey.id)
        if form.is_valid():
            user = request.user  # Get the current authenticated user
            #for question in Question.objects.filter(survey_id=survey_id):
            for question in Question.objects.filter(survey_id=PMH_survey.id):
                selected_option = form.cleaned_data[f'question_{question.id}']
                selected_option_id = Option.objects.get(id=selected_option.id)
                Response.objects.update_or_create(
                    survey=PMH_survey,
                    user=request.user,
                    question=question,
                    defaults={'selected_options': selected_option_id.option}
                )
            return redirect('profile')  # Redirect to a thank-you page after successful submission
    else:
        #form = SurveyForm(survey_id=survey_id)
        form = HistorySurveyForm(initial=initial_data, survey_id=PMH_survey.id)


    demographic_survey = get_object_or_404(Survey, title=DEMOGRAPHIC_SURVEY)

    if demographic_survey is None:
        return render(request, 'survey/error.html', {'message': 'No survey available.'})
    
    # Fetch existing responses for this user and survey
    existing_responses = Response.objects.filter(survey=demographic_survey, user=request.user)
    initial_data = {}
    if existing_responses.exists():
        for response in existing_responses:
            field_name = f'question_{response.question.id}'
            # Find the Option object that matches the response text
            try:
                selected_option = Option.objects.get(question=response.question, option=response.selected_options)
                initial_data[field_name] = selected_option.id
            except Option.DoesNotExist:
                # Handle the case where the option does not exist
                pass

    print('initial_data :: ', initial_data)
    
    if request.method == 'POST':
        #form = SurveyForm(request.POST, survey_id=survey_id)
        demographic_form = DemographicSurveyForm(request.POST, survey_id=demographic_survey.id)
        if demographic_form.is_valid():
            user = request.user  # Get the current authenticated user
            #for question in Question.objects.filter(survey_id=survey_id):
            for question in Question.objects.filter(survey_id=demographic_survey.id):
                selected_option = demographic_form.cleaned_data[f'question_{question.id}']
                selected_option_id = Option.objects.get(id=selected_option.id)
                Response.objects.update_or_create(
                    survey=demographic_survey,
                    user=request.user,
                    question=question,
                    defaults={'selected_options': selected_option_id.option}
                )
            return redirect('profile')  # Redirect to a thank-you page after successful submission
    else:
        #form = SurveyForm(survey_id=survey_id)
        demographic_form = DemographicSurveyForm(initial=initial_data, survey_id=demographic_survey.id)
    
    return render(request, 'users/profile.html', {'PMH_survey': PMH_survey, 'demographic_survey': demographic_survey, 'form': form , 'demographic_form': demographic_form})

from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def user_redirect(request):
    print('USER :: ', request.user.is_superuser)
    if request.user.is_superuser: 
        return redirect('vizual-home')
    
    user_profile = request.user.user_profile
    print('User Profile :: ', user_profile.role)
    if user_profile.role == 'mentor':
        return redirect('vizual-home')
    elif user_profile.role == 'mentee':
        return redirect('survey-home')
    else:
        # default redirect or handle unknown role
        return redirect('default-redirect-url')

