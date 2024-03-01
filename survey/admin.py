from django.contrib import admin
from .models import Survey, Question, Option, Response, QuestionCategory, UserComment

# Register your models here.
admin.site.register(Survey)
admin.site.register(Question)
admin.site.register(Option)
admin.site.register(Response)
admin.site.register(QuestionCategory)
admin.site.register(UserComment)
