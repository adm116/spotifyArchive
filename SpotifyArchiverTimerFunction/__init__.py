import datetime
import logging

import azure.functions as func

import spotipy
from SpotifyArchiverTimerFunction.archiver import Archiver
from SpotifyArchiverTimerFunction.constants import *

# create spotipy class to use
def createSpotipyClass(token):
    return spotipy.Spotify(auth=token)

# Generate a token
def getToken():
    sp_oauth = spotipy.oauth2.SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET, redirect_uri=SPOTIFY_REDIRECT_URL, scope=SCOPE)
    token = sp_oauth.refresh_access_token(REFRESH_TOKEN).get('access_token')
    return token

def main(mytimer: func.TimerRequest) -> None:
    utc_timestamp = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc).isoformat()
    
    token = getToken()
    spotipyClass = createSpotipyClass(token)
    archiver = Archiver(spotipyClass)
    archiver.archive()

    if mytimer.past_due:
        logging.info('The timer is past due!')

    logging.info('Python timer trigger function ran at %s', utc_timestamp)
