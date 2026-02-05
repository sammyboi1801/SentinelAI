import base64
from email.message import EmailMessage
from sentinel.tools.gmail_auth import get_gmail_service
import os



def send_email(to, subject, body):
    if not os.path.exists('credentials.json') and not os.path.exists('token.json'):
        return "Error: Missing 'credentials.json'. Please setup Google OAuth first."

    try:
        service = get_gmail_service()

        # Create the email
        message = EmailMessage()
        message.set_content(body)
        message['To'] = to
        message['Subject'] = subject

        # Encode the message (Base64 required by Gmail API)
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}

        # Send
        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        return f"Email sent! ID: {send_message['id']}"
    except Exception as e:
        return f"Error sending email: {e}"


def read_emails(limit=5):
    if not os.path.exists('credentials.json') and not os.path.exists('token.json'):
        return "Error: Missing 'credentials.json'. Please setup Google OAuth first."

    try:
        service = get_gmail_service()

        # List messages (INBOX only)
        results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=limit).execute()
        messages = results.get('messages', [])

        if not messages:
            return "No emails found."

        email_summaries = []
        for msg in messages:
            # Fetch full details for each ID
            txt = service.users().messages().get(userId='me', id=msg['id']).execute()

            # Extract Headers
            headers = txt['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown")
            snippet = txt.get('snippet', '')

            email_summaries.append(f"FROM: {sender}\nSUBJECT: {subject}\nSNIPPET: {snippet}\n")

        return "\n---\n".join(email_summaries)

    except Exception as e:
        return f"Error reading emails: {e}"