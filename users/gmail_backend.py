import base64
from email.message import EmailMessage
from django.core.mail.backends.base import BaseEmailBackend
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from django.conf import settings
import os
import logging
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
]

class GmailBackend(BaseEmailBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.creds = None
        self.service = None
        self._authenticate_gmail()

    def _authenticate_gmail(self):
        try:
            # Get the directory where this file (gmail_backend.py) is located
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Construct the full path to the credentials.json file
            credentials_path = os.path.join(base_dir, "credentials.json")
            token_path = os.path.join(base_dir, "token.json")

            if os.path.exists(token_path):
                self.creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
                    self.creds = flow.run_local_server(port=0)
                # Save the credentials for the next run
                with open(token_path, "w") as token:
                    token.write(self.creds.to_json())

            self.service = build("gmail", "v1", credentials=self.creds)
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            self.service = None
        except Exception as e:
            logger.error(f"An error occurred during authentication: {e}")
            self.service = None

    def send_password_reset(self, request, email):
        try:
            user = User.objects.get(email=email)
            current_site = get_current_site(request)
            uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_link = f"http://{current_site.domain}/update_password/{uidb64}/{token}/"

            logger.info(f'Reset Link: {reset_link}')
            
            # Create the email message
            subject = settings.EMAIL_SUBJECT
            html_content = render_to_string('users/password_reset_email.html', {
                'user': user,
                'reset_url': reset_link,
            })

            # Manually create the MIME structure
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = settings.EMAIL_HOST_USER
            message['To'] = user.email

            # Attach the HTML content
            mime_text = MIMEText(html_content, 'html')
            message.attach(mime_text)

            # Send the email using Gmail API
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {"raw": encoded_message}

            send_message = (
                self.service.users().messages().send(userId="me", body=create_message).execute()
            )
            logger.info(f'Email sent successfully, Message Id: {send_message["id"]}')
            return True
        except User.DoesNotExist:
            logger.error("No user found with this email address.")
            return False
        except HttpError as error:
            logger.error(f"An error occurred while sending email: {error}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return False
