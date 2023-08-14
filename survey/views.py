from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Survey, Question, Option, Response
from .forms import SurveyForm


'''
def survey_home(request):
    return render(request, 'survey/survey.html', {'title': 'Survey'})
'''

@login_required
#def survey_home(request, survey_id):
def survey_home(request):
    #survey = Survey.objects.get(id=survey_id)
    survey = Survey.objects.all().first()
    if request.method == 'POST':
        #form = SurveyForm(request.POST, survey_id=survey_id)
        form = SurveyForm(request.POST, survey_id=survey.id)
        if form.is_valid():
            user = request.user  # Get the current authenticated user
            #for question in Question.objects.filter(survey_id=survey_id):
            for question in Question.objects.filter(survey_id=survey.id):
                selected_option = form.cleaned_data[f'question_{question.id}']
                selected_option_id = Option.objects.get(id=selected_option.id)
                response = Response.objects.create(
                    survey=survey,
                    user=user,
                    question=question,
                    selected_options=selected_option_id.option  # Store the option's text, not the Option object
                )
            return redirect('thank_you')  # Redirect to a thank-you page after successful submission
    else:
        #form = SurveyForm(survey_id=survey_id)
        form = SurveyForm(survey_id=survey.id)
    
    return render(request, 'survey/survey.html', {'survey': survey, 'form': form})

def thank_you_view(request):
    return render(request, 'survey/thank_you.html')
