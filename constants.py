import os

# spotify security scopes
SCOPE = 'user-library-read playlist-read-private playlist-modify-private playlist-modify-public'

# whether to create new playlists as public
CREATE_PUBLIC_PLAYLISTS = bool(os.environ['CREATE_PUBLIC_PLAYLISTS'])

# Server-side Parameters
PORT = os.environ['PORT']
SLEEP_TIME = int(os.environ['SLEEP_TIME'])

# spotify constraints
LIKED_TRACKS_MAX = 20
PLAYLISTS_REQUEST_MAX = 50
TRACKS_TO_ADD_REQUEST_MAX = 100
TRACKS_IN_PLAYLIST_REQUEST_MAX = 100

# spotify app credentials
SPOTIFY_USERNAME = os.environ['SPOTIFY_USERNAME']
SPOTIFY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
SPOTIFY_REDIRECT_URL = os.environ['SPOTIFY_REDIRECT_URL']
REFRESH_TOKEN = os.environ['REFRESH_TOKEN']