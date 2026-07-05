"""
Run this ONCE locally to authenticate with your NEW OAuth client and
generate a fresh token.pickle. This will open a browser window asking
you to log into the Google account that owns your YouTube channel.

After running this, run extract_refresh_token.py to get the refresh
token for the YOUTUBE_REFRESH_TOKEN GitHub secret.

Requires: pip install google-auth-oauthlib --break-system-packages

Usage:
  python local_auth_setup.py
(Run from the folder containing your NEW client_secret.json)
"""

import pickle
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
CLIENT_SECRET_FILE = "client_secret.json"  # make sure this is the NEW one
TOKEN_FILE = "token.pickle"

flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
# access_type='offline' + prompt='consent' ensures Google actually issues
# a refresh_token (not just a short-lived access token)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

with open(TOKEN_FILE, "wb") as f:
    pickle.dump(creds, f)

print(f"\nSaved fresh {TOKEN_FILE}, authenticated against the new client.")
print("Next: run `python extract_refresh_token.py` to get your refresh token.")
