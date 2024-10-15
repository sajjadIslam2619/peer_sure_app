import csv
from django.http import HttpResponse
from django.contrib import admin
from .models import Survey, Question, Option, Response, QuestionCategory, UserComment, SurveyCategory

# Export Survey model data to CSV
def export_surveys_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="surveys.csv"'

    writer = csv.writer(response)
    # Write the header for Survey fields
    writer.writerow(['ID', 'Title', 'Description', 'Created At', 'Updated At', 'Organization', 'Category'])

    # Write the data rows
    for survey in queryset:
        writer.writerow([survey.id, survey.title, survey.description, survey.created_at, survey.updated_at, survey.organization.name, survey.category.category])

    return response

export_surveys_to_csv.short_description = 'Export selected Surveys to CSV'


# Export Question model data to CSV
def export_questions_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="questions.csv"'

    writer = csv.writer(response)
    # Write the header for Question fields
    writer.writerow(['ID', 'Survey', 'Question', 'Weight', 'Orientation', 'Created At', 'Updated At'])

    # Write the data rows
    for question in queryset:
        writer.writerow([question.id, question.survey.title, question.question, question.weight, question.orientation, question.created_at, question.updated_at])

    return response

export_questions_to_csv.short_description = 'Export selected Questions to CSV'


# Export Option model data to CSV
def export_options_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="options.csv"'

    writer = csv.writer(response)
    # Write the header for Option fields
    writer.writerow(['ID', 'Option', 'Created At', 'Updated At'])

    # Write the data rows
    for option in queryset:
        writer.writerow([option.id, option.option, option.created_at, option.updated_at])

    return response

export_options_to_csv.short_description = 'Export selected Options to CSV'


# Export Response model data to CSV
def export_responses_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="responses.csv"'

    writer = csv.writer(response)
    # Write the header for Response fields
    writer.writerow(['ID', 'Survey Title', 'User', 'Question', 'Selected Options', 'Date Responded', 'Created At', 'Updated At'])

    # Write the data rows
    for response_obj in queryset:
        writer.writerow([
            response_obj.id, 
            response_obj.survey.title, 
            response_obj.user.username, 
            response_obj.question.question, 
            response_obj.selected_options,  # This is assumed to be a text field
            response_obj.date_responsed, 
            response_obj.created_at, 
            response_obj.updated_at
        ])

    return response

export_responses_to_csv.short_description = 'Export selected Responses to CSV'


# Export UserComment model data to CSV
def export_user_comments_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="user_comments.csv"'

    writer = csv.writer(response)
    # Write the header for UserComment fields
    writer.writerow(['ID', 'Survey', 'User', 'Comment', 'Date Commented', 'Created At', 'Updated At'])

    # Write the data rows
    for comment in queryset:
        writer.writerow([comment.id, comment.survey.title, comment.user.username, comment.comment, comment.date_commented, comment.created_at, comment.updated_at])

    return response

export_user_comments_to_csv.short_description = 'Export selected User Comments to CSV'


# Export SurveyCategory model data to CSV
def export_survey_categories_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="survey_categories.csv"'

    writer = csv.writer(response)
    # Write the header for SurveyCategory fields
    writer.writerow(['ID', 'Category', 'Created At', 'Updated At'])

    # Write the data rows
    for category in queryset:
        writer.writerow([category.id, category.category, category.created_at, category.updated_at])

    return response

export_survey_categories_to_csv.short_description = 'Export selected Survey Categories to CSV'


# Export QuestionCategory model data to CSV
def export_question_categories_to_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="question_categories.csv"'

    writer = csv.writer(response)
    # Write the header for QuestionCategory fields
    writer.writerow(['ID', 'Category', 'Created At', 'Updated At'])

    # Write the data rows
    for category in queryset:
        writer.writerow([category.id, category.category, category.created_at, category.updated_at])

    return response

export_question_categories_to_csv.short_description = 'Export selected Question Categories to CSV'


# Register the actions in the Admin interface
class SurveyAdmin(admin.ModelAdmin):
    actions = [export_surveys_to_csv]

class QuestionAdmin(admin.ModelAdmin):
    actions = [export_questions_to_csv]

class OptionAdmin(admin.ModelAdmin):
    actions = [export_options_to_csv]

class ResponseAdmin(admin.ModelAdmin):
    actions = [export_responses_to_csv]

class UserCommentAdmin(admin.ModelAdmin):
    actions = [export_user_comments_to_csv]

class SurveyCategoryAdmin(admin.ModelAdmin):
    actions = [export_survey_categories_to_csv]

class QuestionCategoryAdmin(admin.ModelAdmin):
    actions = [export_question_categories_to_csv]

# Register the models and their respective admin classes
admin.site.register(Survey, SurveyAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Option, OptionAdmin)
admin.site.register(Response, ResponseAdmin)
admin.site.register(UserComment, UserCommentAdmin)
admin.site.register(SurveyCategory, SurveyCategoryAdmin)
admin.site.register(QuestionCategory, QuestionCategoryAdmin)