#🇳‌🇮‌🇰‌🇭‌🇮‌🇱‌
# Add your details here and then deploy by clicking on HEROKU Deploy button
import os
from os import environ

API_ID = int(environ.get("API_ID", "29426008"))
API_HASH = environ.get("API_HASH", "fedd630ba4bd77044ee4e5a00e5300e6")
BOT_TOKEN = environ.get("BOT_TOKEN", "8073062375:AAGIoV1G105SCWyru46qhkr8wqHIZYdYvnQ")

OWNER = int(environ.get("OWNER", "8293228865"))
CREDIT = environ.get("CREDIT", "Z E Y A")

TOTAL_USER = os.environ.get('TOTAL_USERS', '8293228865').split(',')
TOTAL_USERS = [int(user_id) for user_id in TOTAL_USER]

AUTH_USER = os.environ.get('AUTH_USERS', '8293228865').split(',')
AUTH_USERS = [int(user_id) for user_id in AUTH_USER]
if int(OWNER) not in AUTH_USERS:
    AUTH_USERS.append(int(OWNER))
  
#WEBHOOK = True  # Don't change this
#PORT = int(os.environ.get("PORT", 8080))  # Default to 8000 if not set




