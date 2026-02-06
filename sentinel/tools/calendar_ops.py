import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import tzlocal

from sentinel.paths import CREDENTIALS_PATH as CREDS_FILE, TOKEN_PATH as TOKEN_FILE

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar'
]


def get_service():
    """Handles Authentication for both Gmail and Calendar."""
    creds = None

    # Load existing token
    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

    # Refresh or login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDS_FILE.exists():
                return None

            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDS_FILE),
                SCOPES
            )
            creds = flow.run_local_server(port=0)

        # Save token
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)


def list_upcoming_events(max_results=10):
    try:
        service = get_service()
        if not service:
            return f"Error: credentials.json missing.\nPlace it at:\n{CREDS_FILE}"

        now = datetime.datetime.utcnow().isoformat() + 'Z'

        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        if not events:
            return "No upcoming events found."

        output = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            summary = event.get('summary', 'No Title')
            output.append(f"- {start}: {summary}")

        return "\n".join(output)

    except Exception as e:
        return f"Calendar Error: {e}"


def get_events_in_frame(start_iso, end_iso):
    try:
        service = get_service()
        if not service:
            return f"Error: credentials.json missing.\nPlace it at:\n{CREDS_FILE}"

        if not start_iso.endswith("Z"):
            start_iso += "Z"
        if not end_iso.endswith("Z"):
            end_iso += "Z"

        events_result = service.events().list(
            calendarId='primary',
            timeMin=start_iso,
            timeMax=end_iso,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        if not events:
            return "No events in that range."

        return "\n".join([
            f"- {e['start'].get('dateTime', e['start'].get('date'))}: {e.get('summary')}"
            for e in events
        ])

    except Exception as e:
        return f"Error: {e}"


def create_event(summary, start_time, duration_mins=60, description=""):
    try:
        service = get_service()
        if not service:
            return f"Error: credentials.json missing.\nPlace it at:\n{CREDS_FILE}"

        start_time = start_time.replace("Z", "")
        start_dt = datetime.datetime.fromisoformat(start_time)
        end_dt = start_dt + datetime.timedelta(minutes=int(duration_mins))

        local_tz = tzlocal.get_localzone_name()

        event = {
            'summary': summary,
            'description': description,
            'start': {
                'dateTime': start_dt.isoformat(),
                'timeZone': local_tz,
            },
            'end': {
                'dateTime': end_dt.isoformat(),
                'timeZone': local_tz,
            },
        }

        event = service.events().insert(
            calendarId='primary',
            body=event
        ).execute()

        return f"Event created: {event.get('htmlLink')}"

    except Exception as e:
        return f"Error creating event: {e}"


def quick_add(text):
    try:
        service = get_service()
        if not service:
            return f"Error: credentials.json missing.\nPlace it at:\n{CREDS_FILE}"

        created_event = service.events().quickAdd(
            calendarId='primary',
            text=text
        ).execute()

        return f"Quick event created: {created_event.get('htmlLink')}"

    except Exception as e:
        return f"Error: {e}"