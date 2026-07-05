"""
Run this ONCE locally to print your refresh token, so you can paste it into
GitHub → Settings → Secrets and variables → Actions → YOUTUBE_REFRESH_TOKEN.

Do NOT commit this script's output anywhere. Do NOT paste the printed token
into chat, a commit message, or any file that gets pushed to the repo.

Usage: python extract_refresh_token.py
(Run this from the folder containing token.pickle)
"""

import pickle

with open("token.pickle", "rb") as f:
    creds = pickle.load(f)

if not creds.refresh_token:
    print("No refresh token found in token.pickle.")
    print("Delete token.pickle and re-run your upload script once locally")
    print("to force a fresh OAuth consent (make sure access_type='offline'")
    print("and prompt='consent' are set in the auth flow), then re-run this script.")
else:
    print("\nCopy everything between the lines below into the")
    print("YOUTUBE_REFRESH_TOKEN GitHub secret. Do not paste it anywhere else.\n")
    print("-" * 60)
    print(creds.refresh_token)
    print("-" * 60)
