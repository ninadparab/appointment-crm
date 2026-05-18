import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

class ZohoAuthManager:
    def __init__(self):
        self.client_id = os.getenv("ZOHO_CLIENT_ID")
        self.client_secret = os.getenv("ZOHO_CLIENT_SECRET")
        self.refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")
        self.access_token = os.getenv("ZOHO_ACCESS_TOKEN")
        self.api_domain = os.getenv("ZOHO_API_DOMAIN")
        self.token_expiry = datetime.now() + timedelta(hours=1)

    def refresh_access_token(self):
        print("Access token expired, refreshing...")
        response = requests.post(
            "https://accounts.zoho.com/oauth/v2/token",
            params={
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token"
            }
        )
        data = response.json()

        if "access_token" in data:
            self.access_token = data["access_token"]
            self.token_expiry = datetime.now() + timedelta(hours=1)
            
            # Update .env file with new token
            self._update_env("ZOHO_ACCESS_TOKEN", self.access_token)
            print("Token refreshed successfully!")
        else:
            raise Exception(f"Failed to refresh token: {data}")

    def get_valid_token(self):
        # If token expires in less than 5 minutes, refresh it
        if datetime.now() >= self.token_expiry - timedelta(minutes=5):
            self.refresh_access_token()
        return self.access_token

    def _update_env(self, key, value):
        # Read current .env file
        with open(".env", "r") as f:
            lines = f.readlines()
        
        # Update the specific key
        with open(".env", "w") as f:
            for line in lines:
                if line.startswith(f"{key}="):
                    f.write(f"{key}={value}\n")
                else:
                    f.write(line)

    def get_headers(self):
        return {
            "Authorization": f"Zoho-oauthtoken {self.get_valid_token()}",
            "Content-Type": "application/json"
        }