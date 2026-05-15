import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_tokens(authorization_code):
    response = requests.post(
        "https://accounts.zoho.com/oauth/v2/token",
        params={
            "code": authorization_code,
            "client_id": os.getenv("ZOHO_CLIENT_ID"),
            "client_secret": os.getenv("ZOHO_CLIENT_SECRET"),
            "redirect_uri": "https://www.zoho.com",
            "grant_type": "authorization_code"
        }
    )
    return response.json()

# Paste your code here
authorization_code = "1000.978cb761ace6e546921d70c66ccb6834.94ea2cf6165db33a8daf40d8ca004acc"

tokens = get_tokens(authorization_code)
print(tokens)