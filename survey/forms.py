from django import forms
from .models import Question, Survey, Option, Response

class SurveyForm(forms.ModelForm):
    class Meta:
        model = Response
        fields = []
    def __init__(self, *args, **kwargs):
        survey_id = kwargs.pop('survey_id')
        super(SurveyForm, self).__init__(*args, **kwargs)
        questions = Question.objects.filter(survey_id=survey_id)
        for question in questions:
            self.fields[f'question_{question.id}'] = forms.ModelChoiceField(
                label=question.question,
                queryset=Option.objects.filter(question=question),
                widget=forms.RadioSelect,
                required=False
            )
        