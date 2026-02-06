import base64
from email.message import EmailMessage
from googleapiclient.errors import HttpError
from sentinel.paths import CREDENTIALS_PATH, TOKEN_PATH
from sentinel.tools.gmail_auth import get_gmail_service

def send_email(to, subject, body, html=False):
    """
    Sends an email using the centralized Sentinel credentials.
    """
    if not CREDENTIALS_PATH.exists() and not TOKEN_PATH.exists():
        return (f"❌ Error: Missing credentials.\n"
                f"Please place 'credentials.json' in {CREDENTIALS_PATH.parent}\n"
                f"or run the setup command.")

    try:
        service = get_gmail_service()

        message = EmailMessage()
        message['To'] = to
        message['Subject'] = subject
        message.set_content(body)

        if html:
            message.add_alternative(body, subtype='html')

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}

        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        return f"✅ Email sent successfully! (ID: {send_message['id']})"

    except HttpError as error:
        return f"❌ Gmail API Error: {error}"
    except Exception as e:
        return f"❌ System Error: {e}"


def read_emails(limit=5):
    """
    Reads the latest N emails from the Inbox.
    """
    if not CREDENTIALS_PATH.exists() and not TOKEN_PATH.exists():
        return (f"❌ Error: Missing credentials.\n"
                f"Please place 'credentials.json' in {CREDENTIALS_PATH.parent}")

    try:
        service = get_gmail_service()
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=limit).execute()
        messages = results.get('messages', [])

        if not messages:
            return "No new emails found."

        email_summaries = []

        for msg in messages:
            txt = service.users().messages().get(userId='me', id=msg['id'], format='metadata').execute()

            headers = txt['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
            snippet = txt.get('snippet', 'No preview available.')

            email_summaries.append(f"📩 FROM: {sender}\n   SUBJECT: {subject}\n   PREVIEW: {snippet}\n")

        return "\n".join(email_summaries)

    except Exception as e:
        return f"❌ Error reading emails: {e}"