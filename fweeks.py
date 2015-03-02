from datetime import datetime, timedelta
import httplib2
import os
import sys
import sqlite3

from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run
from optparse import OptionParser

CLIENT_SECRETS_FILE = "client_secrets.json"

YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.readonly",
  "https://www.googleapis.com/auth/yt-analytics.readonly"]
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
YOUTUBE_ANALYTICS_API_SERVICE_NAME = "youtubeAnalytics"
YOUTUBE_ANALYTICS_API_VERSION = "v1"

# Helpful message to display if the CLIENT_SECRETS_FILE is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the APIs Console
https://code.google.com/apis/console#access

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
  message=MISSING_CLIENT_SECRETS_MESSAGE,
  scope=" ".join(YOUTUBE_SCOPES))

storage = Storage("%s-oauth2_myapp.json" % sys.argv[0])
credentials = storage.get()

if credentials is None or credentials.invalid:
  credentials = run(flow, storage)

http = credentials.authorize(httplib2.Http())
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, http=http)
youtube_analytics = build(YOUTUBE_ANALYTICS_API_SERVICE_NAME,
  YOUTUBE_ANALYTICS_API_VERSION, http=http)

channels_response = youtube.channels().list(
  mine=True,
  part="id"
).execute()

with sqlite3.connect()