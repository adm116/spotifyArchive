import sys
import spotipy
from datetime import datetime, timedelta
from constants import *
from collections import defaultdict

import time

# ceate a new playlist with the name
def createNewPlaylist(playlistName, spotipyClass):
    newPlaylist = spotipyClass.user_playlist_create(
        user=SPOTIFY_USERNAME, name=playlistName, public=CREATE_PUBLIC_PLAYLISTS)
    return newPlaylist['id']

# return all user playlists
def getExistingPlaylists(spotipyClass):
    exisitingPlaylists = []

    exisitingPlaylistObjects = spotipyClass.user_playlists(
        user=SPOTIFY_USERNAME, limit=PLAYLISTS_REQUEST_MAX, offset=0)
    exisitingPlaylists += exisitingPlaylistObjects['items']

    # in case user has more than PLAYLISTS_REQUEST_MAX playlists, request in PLAYLISTS_REQUEST_MAX
    # sized chunks
    totalNumPlaylists = exisitingPlaylistObjects['total']
    for offset in range(PLAYLISTS_REQUEST_MAX, totalNumPlaylists, PLAYLISTS_REQUEST_MAX):
        exisitingPlaylistObjects = spotipyClass.user_playlists(
            user=SPOTIFY_USERNAME, limit=PLAYLISTS_REQUEST_MAX, offset=offset)
        exisitingPlaylists += exisitingPlaylistObjects['items']

    return exisitingPlaylists

# get playlist by name
def getPlaylistByName(playlistName, spotipyClass):
    existingPlaylists = getExistingPlaylists(spotipyClass)

    for playlist in existingPlaylists:
        if playlist['name'] == playlistName:
            return playlist['id']

    return None

# find existing playlist by name, else create one
def getPlaylistToAddTo(playlistName, spotipyClass):
    playlistId = getPlaylistByName(playlistName, spotipyClass)

    if not playlistId:
        playlistId = createNewPlaylist(playlistName, spotipyClass)

    return playlistId

# get tracks in playlist
def getExistingTrackIdsInPlaylist(playlistId, spotipyClass):
    tracksInPlaylist = []

    tracksInPlaylistObject = spotipyClass.user_playlist_tracks(
        user=SPOTIFY_USERNAME, playlist_id=playlistId, limit=TRACKS_IN_PLAYLIST_REQUEST_MAX, offset=0)

    tracksInPlaylist += tracksInPlaylistObject['items']
    totalNumTracks = tracksInPlaylistObject['total']

    for offset in range(TRACKS_IN_PLAYLIST_REQUEST_MAX, totalNumTracks, TRACKS_IN_PLAYLIST_REQUEST_MAX):
        tracksInPlaylistObject = spotipyClass.user_playlist_tracks(
            user=SPOTIFY_USERNAME, playlist_id=playlistId, limit=TRACKS_IN_PLAYLIST_REQUEST_MAX, offset=offset)
        tracksInPlaylist += tracksInPlaylistObject['items']

    return [track['track']['id'] for track in tracksInPlaylist]

# get tracks to add
def getTracksToAdd(spotipyClass):
    trackTimeObjectsToAdd = []

    # start with only 1 track in otder to get total number in request
    response = spotipyClass.current_user_saved_tracks(limit=1, offset=0)
    totalNumLikedTracks = response['total']

    # request in chunks
    for offset in range(0, totalNumLikedTracks, LIKED_TRACKS_MAX):
        response = spotipyClass.current_user_saved_tracks(limit=LIKED_TRACKS_MAX, offset=offset)
        tracks = response['items']

        for track in tracks:
            timeAdded = datetime.strptime(track['added_at'], '%Y-%m-%dT%H:%M:%SZ')
            oneDayAgo = datetime.utcnow() - timedelta(days=1)

            # if added more than one day ago, we are done (assumes tracks are returned in order)
            if timeAdded < oneDayAgo:
                return trackTimeObjectsToAdd

            trackId = track['track']['id']
            trackTimeObjectsToAdd.append((trackId, timeAdded))

    return trackTimeObjectsToAdd

# add tracks to playlist
def addTracksToPlaylist(playlistId, trackIds, spotipyClass):
    for offset in range(0, len(trackIds), TRACKS_TO_ADD_REQUEST_MAX):
        spotipyClass.user_playlist_add_tracks(
            user=SPOTIFY_USERNAME,
            playlist_id=playlistId,
            tracks=trackIds[offset:min(offset+TRACKS_TO_ADD_REQUEST_MAX, len(trackIds))])

# create spotipy class to use
def createSpotipyClass(token):
    return spotipy.Spotify(auth=token)

# Generate a token
def getToken():
    sp_oauth = spotipy.oauth2.SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET, redirect_uri=SPOTIFY_REDIRECT_URL, scope=SCOPE)
    token = sp_oauth.refresh_access_token(REFRESH_TOKEN).get('access_token')
    return token

# map from playlist names to tracks
def getPlaylistMapping(trackTimeObjects):
    playlistMap = defaultdict(list)

    for id, timeAdded in trackTimeObjects:
        fullYear = timeAdded.strftime("%Y")
        shortYear = timeAdded.strftime("%y")
        fullMonth = timeAdded.strftime("%B")

        # playlist archive names
        monthArchiveName = fullMonth + " \'" + shortYear
        yearArchiveName = fullYear

        playlistMap[monthArchiveName].append(id)
        playlistMap[yearArchiveName].append(id)

    return playlistMap

# remove the existing tracks
def removeExistingTrackIds(existingTrackIdsInPlaylist, trackIds):
    toReturn = []

    for trackId in trackIds:
        if trackId not in existingTrackIdsInPlaylist:
            toReturn.append(trackId)

    return toReturn

while True:
    token = getToken()
    spotipyClass = createSpotipyClass(token)

    trackTimeObjects = getTracksToAdd(spotipyClass)
    playlistToTracksMap = getPlaylistMapping(trackTimeObjects)

    for playlistName, trackIds in playlistToTracksMap.items():
        playlistId = getPlaylistToAddTo(playlistName, spotipyClass)
        existingTrackIdsInPlaylist = set(getExistingTrackIdsInPlaylist(playlistId, spotipyClass))
        trackIdsToAdd = removeExistingTrackIds(existingTrackIdsInPlaylist, trackIds)
        addTracksToPlaylist(playlistId, trackIdsToAdd, spotipyClass)

    time.sleep(SLEEP_TIME)