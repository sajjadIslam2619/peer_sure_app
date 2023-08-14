from django import forms
from .models import Comment
from django.utils.translation import gettext_lazy as _


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']

        labels = {
            'content': _(''),
        }

        widgets = {
            'content' : forms.Textarea(attrs={'rows': 4}),
        }