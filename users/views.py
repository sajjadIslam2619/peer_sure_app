from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserProfileForm, HistorySurveyForm
from django.views.decorators.csrf import csrf_exempt
from survey.models import Survey, Question, Option, Response
from peer_sure_app.settings import CHECK_IN_SURVEY, PAST_HISTORY_SURVEY



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
    surveys = Survey.objects.all()
    for survey_obj in surveys:
        if survey_obj.title == PAST_HISTORY_SURVEY:
            print("Survey Title:", survey_obj.title)
            survey = survey_obj
            break

    if survey is None:
        return render(request, 'survey/error.html', {'message': 'No survey available.'})
    
    # Fetch existing responses for this user and survey
    existing_responses = Response.objects.filter(survey=survey, user=request.user)
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
        form = HistorySurveyForm(request.POST, survey_id=survey.id)
        if form.is_valid():
            user = request.user  # Get the current authenticated user
            #for question in Question.objects.filter(survey_id=survey_id):
            for question in Question.objects.filter(survey_id=survey.id):
                selected_option = form.cleaned_data[f'question_{question.id}']
                selected_option_id = Option.objects.get(id=selected_option.id)
                Response.objects.update_or_create(
                    survey=survey,
                    user=request.user,
                    question=question,
                    defaults={'selected_options': selected_option_id.option}
                )
            return redirect('profile')  # Redirect to a thank-you page after successful submission
    else:
        #form = SurveyForm(survey_id=survey_id)
        form = HistorySurveyForm(initial=initial_data, survey_id=survey.id)
    
    return render(request, 'users/profile.html', {'survey': survey, 'form': form})