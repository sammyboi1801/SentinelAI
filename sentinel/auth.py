# sentinel/auth.py

from google_auth_oauthlib.flow import InstalledAppFlow
from sentinel.paths import CREDS_FILE, TOKEN_FILE

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/calendar'
]


def fix_authentication():
    print("--- SENTINEL GOOGLE AUTH ---\n")

    if not CREDS_FILE.exists():
        print("❌ credentials.json not found.\n")
        print("Download it from Google Cloud Console and place it here:\n")
        print(CREDS_FILE)
        return

    if TOKEN_FILE.exists():
        print("⚠ Found old token. Deleting...")
        TOKEN_FILE.unlink()

    print("Opening browser for Google login...\n")

    flow = InstalledAppFlow.from_client_secrets_file(
        str(CREDS_FILE),
        SCOPES
    )

    creds = flow.run_local_server(port=0)

    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print("\n✅ Authentication complete.")
    print("Token saved to:")
    print(TOKEN_FILE)