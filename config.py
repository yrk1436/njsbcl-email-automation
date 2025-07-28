"""
Configuration settings for the biweekly task automation.
"""

import os
from datetime import time

# URLs
SCHEDULE_URL = "https://cricclubs.com/NJSBCL/fixtures.do?league=56&teamId=3264&internalClubId=null&year=2025&clubId=2690"
CONTACTS_URL = "https://xyz.com/contacts"

# Files
CONTACTS_FILE = "contacts.txt"
MAP_IMAGE_PATH = "assets/cricket_pitch_map.jpg"  # Path to the map image

# Team information
TEAM_NAME = "SPARTA XI"
SPARTA_MAP_LINK = "https://maps.app.goo.gl/6sYdMjgKkR1ZCMya9?g_st=com.google.maps.preview.copy"  # Static map link

# Email settings
EMAIL_TEMPLATE_FILE = "email_template.html"
GMAIL_CREDENTIALS_FILE = "credentials.json"
GMAIL_TOKEN_FILE = "token.json"
GMAIL_SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# CC emails (comma-separated)
CC_EMAILS = "yrk1436@gmail.com,sumanmaram@gmail.com,piyushparashar.rv@gmail.com"

# Email scheduling
EMAIL_SEND_TIME = time(19, 0)  # 7:00 PM ET
EMAIL_SEND_DAY = "Tuesday"  # Send on Tuesday before Sunday game

# Email subject format
EMAIL_SUBJECT_FORMAT = "SPARTA XI VS {OPPONENT_TEAM}"

# Ollama settings
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "gemma3:4b"  # or any other model you have
OLLAMA_TIMEOUT = 60

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# HTTP settings
REQUEST_TIMEOUT = 60
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# Date format for parsing
DATE_FORMAT = "%Y-%m-%d"
DISPLAY_DATE_FORMAT = "%A, %B %d"  # e.g., "Sunday, July 27" 