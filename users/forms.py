from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UserProfileForm(forms.ModelForm):
    #mentor_email = forms.EmailField(widget=forms.EmailInput(attrs={'placeholder': 'Please enter your mentor\'s email here, if you have a mentor. Otherwise you will be assigned a mentor later.'}))
    class Meta:
        model = UserProfile
        fields = ['role', 'mentor_email']


from survey.models import Question, Survey, Option, Response

class HistorySurveyForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = []

    def __init__(self, *args, **kwargs):
        survey_id = kwargs.pop('survey_id')
        initial = kwargs.get('initial', {})
        super(HistorySurveyForm, self).__init__(*args, **kwargs)

        questions = Question.objects.filter(survey_id=survey_id)
        for question in questions:
            field_name = f'question_{question.id}'
            self.fields[field_name] = forms.ModelChoiceField(
                label=question.question,  # Corrected to question.question
                queryset=Option.objects.filter(question=question),
                widget=forms.RadioSelect
            )
            if field_name in initial:
                # Assuming initial[field_name] is the ID of the selected Option
                self.fields[field_name].initial = initial[field_name]
        