"""Loads demo settings from the .env file (see .env.example)."""
import os
import sys

from dotenv import load_dotenv

# Load settings from `.env` and check that all required ones are present.
load_dotenv()

REQUIRED = [
    "AUTH0_DOMAIN",
    "CLIENT_ID",
    "CLIENT_SECRET",
    "PARENT_API",
    "SEARCH_API",
    "SUBJECT_TOKEN_TYPE",
    "TEST_USER",
    "TEST_PASSWORD",
]

missing = [name for name in REQUIRED if not os.getenv(name)]
if missing:
    sys.exit(
        f"Missing settings in .env: {', '.join(missing)}\n"
        "Copy .env.example to .env and fill in the values."
    )

AUTH0_DOMAIN = os.environ["AUTH0_DOMAIN"]
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
PARENT_API = os.environ["PARENT_API"]
SEARCH_API = os.environ["SEARCH_API"]
SUBJECT_TOKEN_TYPE = os.environ["SUBJECT_TOKEN_TYPE"]
TEST_USER = os.environ["TEST_USER"]
TEST_PASSWORD = os.environ["TEST_PASSWORD"]

TOKEN_URL = f"https://{AUTH0_DOMAIN}/oauth/token"