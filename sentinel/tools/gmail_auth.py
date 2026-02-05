import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from sentinel.paths import CREDENTIALS_PATH, TOKEN_PATH

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]


def get_gmail_service():
    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:

            if not os.path.exists(CREDENTIALS_PATH):
                print(f"Error: credentials.json not found at {CREDENTIALS_PATH}")
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)

        with open(TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    from googleapiclient.discovery import build
    return build('gmail', 'v1', credentials=creds)