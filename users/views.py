from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserProfileForm, HistorySurveyForm, DemographicSurveyForm, PasswordResetRequestForm
from django.views.decorators.csrf import csrf_exempt
from survey.models import Survey, Question, Option, Response
from peer_sure_app.settings import (CHECK_IN_SURVEY, PAST_HISTORY_SURVEY, DEMOGRAPHIC_SURVEY, MESSAGE_SURVEY_UNAVAIABLE, 
                                    MESSAGE_SURVEY_PMHx_UNACCESSIBLE, MESSAGE_EMAIL_SEND_FAILED, MESSAGE_PASSWORD_RESET_MISSING_LINK, 
                                    MESSAGE_PASSWORD_UPDATED)
from peer_sure_app.settings import (SURVEY_CATEGORY_CHECK_IN, SURVEY_CATEGORY_PMHx, SURVEY_CATEGORY_DEMOGRAPHY, 
                                    MESSAGE_SURVEY_REQUIRED_SURVEY, MESSAGE_ORGANIZATION_MISSING, MESSAGE_PASSWORD_RESET_INVALID_LINK)
from django.shortcuts import get_object_or_404, render
from django.http import Http404
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.contrib.auth import update_session_auth_hash
from .forms import UserPasswordChangeForm, UpdatePasswordForm
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from .gmail_backend import GmailBackend
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from .models import UserProfile, Organization
import logging
logger = logging.getLogger(__name__)


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

            # Save the many-to-many data for organizations
            profile_form.save_m2m()

            logger.info(f"User {user.username} profile created with role: {profile.role}")
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('survey-home')
    else:
        form = UserRegisterForm()
        profile_form = UserProfileForm()
    return render(request, 'users/register.html', {'form': form, 'profile_form': profile_form})

@login_required
def change_password(request):
    if request.method == 'POST':
        form = UserPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = UserPasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {
        'form': form
    })


#@csrf_exempt
@login_required
def profile(request):
    selected_organization = None
    survey_error_message = None
    
    if not request.user.is_superuser:
        # Retrieve the selected organization from the session
        selected_org_id = request.session.get('selected_organization_id')
        if selected_org_id:
            try:
                selected_organization = Organization.objects.get(id=selected_org_id)
                logger.info(f'Selected Organization :: {selected_organization}')
            except Organization.DoesNotExist:
                # Redirect if the selected organization is not found
                return redirect('organization_selection')
        else:
            user_profile = request.user.user_profile
            organizations = user_profile.organizations.all()
            if organizations.exists():
                # If only one organization is associated with the user, select it
                selected_organization = organizations.first()
                logger.info(f'Selected first organization: {selected_organization}')
            else:
                # Handle the case where the user has no organizations
                logger.info('User has no organizations.')
                messages.info(request, MESSAGE_SURVEY_PMHx_UNACCESSIBLE)
                #return redirect('profile')
        
    try:
        PMH_survey = Survey.objects.filter(
            organization=selected_organization,
            category__category=SURVEY_CATEGORY_PMHx
        ).first()
        if not PMH_survey:
            raise Survey.DoesNotExist
        logger.debug(f'Survey found: {PMH_survey.title} for organization {PMH_survey.organization}')
    except Survey.DoesNotExist:
        logger.debug(f'Survey not available, required survey category: {SURVEY_CATEGORY_PMHx}')
        PMH_survey = None
        survey_error_message = f'{MESSAGE_SURVEY_REQUIRED_SURVEY} {SURVEY_CATEGORY_PMHx}'
    
    '''
    try:
        PMH_survey = get_object_or_404(Survey, title=PAST_HISTORY_SURVEY)
    except Http404:
        logger.debug(f'Survey not available, required survey: {PAST_HISTORY_SURVEY}')
        return render(request, 'users/error.html', {'message': f'Survey not available, required survey: {PAST_HISTORY_SURVEY}'})
    '''
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
        form = HistorySurveyForm(initial=initial_data, survey_id=PMH_survey.id) if PMH_survey else None

    try:
        demographic_survey = get_object_or_404(Survey, title=DEMOGRAPHIC_SURVEY)
    except Http404:
        logger.debug(f'Survey not available, required survey: {DEMOGRAPHIC_SURVEY}')
        return render(request, 'users/error.html', {'message': f'{MESSAGE_SURVEY_REQUIRED_SURVEY} {DEMOGRAPHIC_SURVEY}'})

    if demographic_survey is None:
        return render(request, 'survey/error.html', {'message': MESSAGE_SURVEY_UNAVAIABLE})
    
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
    
    return render(request, 'users/profile.html', {'PMH_survey': PMH_survey, 'demographic_survey': demographic_survey, 
                                                  'form': form , 'demographic_form': demographic_form, 'survey_error_message': survey_error_message})


@login_required
def user_redirect(request):
    logger.info(f"Is superuser:: {request.user.is_superuser}")
    
    # Redirect superuser to vizual-home
    if request.user.is_superuser:
        return redirect('vizual-home')
    
    # Fetch user profile
    user_profile = request.user.user_profile
    logger.info(f"User role :: {user_profile.role}")
    
    # Check User Organizations
    organizations = user_profile.organizations.all()
    
    # If user has multiple organizations, redirect to organization selection view
    if organizations.count() > 1:
        return redirect('organization_selection')
    
    # Handle case where user has one or no organizations
    if organizations.count() == 1:
        selected_organization = organizations.first()  # Get the single organization
        
        # Check if the selected organization is 'No Organization'
        if selected_organization.name == 'No Organization':
            messages.info(request, {MESSAGE_ORGANIZATION_MISSING})
            return redirect('profile')  # Redirect to profile section if 'No Organization' is selected
    
    # Redirect based on user role
    if user_profile.role == 'mentor':
        return redirect('vizual-home')
    elif user_profile.role == 'mentee':
        return redirect('survey-home')
    else:
        # Default redirect
        return redirect('profile')
    
@login_required
def organization_selection(request):
    user_profile = request.user.user_profile
    organizations = user_profile.organizations.all()

    if request.method == 'POST':
        selected_org_id = request.POST.get('organization')
        try:
            selected_organization = organizations.get(id=selected_org_id)

            request.session['selected_organization_id'] = selected_organization.id  # Store selected org in session
            return redirect('user_redirect_after_selection')  # Redirect to new redirect view after selection

        except Organization.DoesNotExist:
            logger.error("Selected organization does not exist or is not assigned to the user.")
            messages.error(request, "Please select a valid organization.")

    return render(request, 'users/organization_selection.html', {'organizations': organizations})

@login_required
def user_redirect_after_selection(request):
    selected_org_id = request.session.get('selected_organization_id')
    if not selected_org_id:
        return redirect('organization_selection')

    # Continue redirection based on role
    user_profile = request.user.user_profile
    if user_profile.role == 'mentor':
        return redirect('vizual-home')
    elif user_profile.role == 'mentee':
        return redirect('survey-home')
    else:
        return redirect('default-redirect-url')

@login_required
def custom_logout(request):
    logout(request)
    #messages.info(request, "You have successfully logged out.")
    return render(request, 'users/logout.html')

def custom_password_reset_view(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            logger.info(f"Email requested for password reset: {email}")
            # Sending the password reset email using GmailBackend
            email_backend = GmailBackend()
            email_sent = email_backend.send_password_reset(request, email)

            if email_sent:
                return render(request, 'users/password_reset_done.html')
            else:
                return render(request, 'users/password_reset.html', {'form': form, 'error': MESSAGE_EMAIL_SEND_FAILED})

        else:
            return render(request, 'users/password_reset.html', {'form': form})
    else:
        form = PasswordResetRequestForm()
    return render(request, 'users/password_reset.html', {'form': form})

def update_password(request, uidb64=None, token=None):
    if uidb64 and token:
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None
            logger.error("User not found or invalid user ID.")
        
        if user is not None and default_token_generator.check_token(user, token):
            if request.method == 'POST':
                form = UpdatePasswordForm(user=user, data=request.POST)
                if form.is_valid():
                    logger.info("Form is valid, attempting to save new password.")
                    user = form.save()
                    update_session_auth_hash(request, user)  # Important to keep the user logged in
                    messages.success(request, MESSAGE_PASSWORD_UPDATED)
                    logger.info("Password updated successfully for user.")
                    return redirect('login')  # Redirect to login after successful reset
                else:
                    logger.error("Form is invalid. Errors: %s", form.errors)
                    messages.error(request, 'Please correct the error below.')
            else:
                form = UpdatePasswordForm(user=user)
            return render(request, 'users/update_password.html', {'form': form})
        else:
            logger.error("The password reset link was invalid or the token has expired.")
            messages.error(request, MESSAGE_PASSWORD_RESET_INVALID_LINK)
            return redirect('login')
    else:
        logger.error("The password reset link is missing.")
        messages.error(request, MESSAGE_PASSWORD_RESET_MISSING_LINK)
        return redirect('login')