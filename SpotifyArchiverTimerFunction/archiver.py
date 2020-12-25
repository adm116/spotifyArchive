import sys
import spotipy
from datetime import datetime, timedelta
from SpotifyArchiverTimerFunction.constants import *
from collections import defaultdict

class Archiver:

    def __init__(self, spotipyClass):
        self.spotipyClass = spotipyClass

    # ceate a new playlist with the name
    def createNewPlaylist(self, playlistName):
        newPlaylist = self.spotipyClass.user_playlist_create(
            user=SPOTIFY_USERNAME, name=playlistName, public=True)
        return newPlaylist['id']

    # return all user playlists
    def getExistingPlaylists(self):
        exisitingPlaylists = []

        exisitingPlaylistObjects = self.spotipyClass.user_playlists(
            user=SPOTIFY_USERNAME, limit=PLAYLISTS_REQUEST_MAX, offset=0)
        exisitingPlaylists += exisitingPlaylistObjects['items']

        # in case user has more than PLAYLISTS_REQUEST_MAX playlists, request in PLAYLISTS_REQUEST_MAX
        # sized chunks
        totalNumPlaylists = exisitingPlaylistObjects['total']
        for offset in range(PLAYLISTS_REQUEST_MAX, totalNumPlaylists, PLAYLISTS_REQUEST_MAX):
            exisitingPlaylistObjects = self.spotipyClass.user_playlists(
                user=SPOTIFY_USERNAME, limit=PLAYLISTS_REQUEST_MAX, offset=offset)
            exisitingPlaylists += exisitingPlaylistObjects['items']

        return exisitingPlaylists

    # get playlist by name
    def getPlaylistByName(self, playlistName):
        existingPlaylists = self.getExistingPlaylists()

        for playlist in existingPlaylists:
            if playlist['name'] == playlistName:
                return playlist['id']

        return None

    # find existing playlist by name, else create one
    def getPlaylistToAddTo(self, playlistName):
        playlistId = self.getPlaylistByName(playlistName)

        if not playlistId:
            playlistId = self.createNewPlaylist(playlistName)

        return playlistId

    # get tracks in playlist
    def getExistingTrackIdsInPlaylist(self, playlistId):
        tracksInPlaylist = []

        tracksInPlaylistObject = self.spotipyClass.user_playlist_tracks(
            user=SPOTIFY_USERNAME, playlist_id=playlistId, limit=TRACKS_IN_PLAYLIST_REQUEST_MAX, offset=0)

        tracksInPlaylist += tracksInPlaylistObject['items']
        totalNumTracks = tracksInPlaylistObject['total']

        for offset in range(TRACKS_IN_PLAYLIST_REQUEST_MAX, totalNumTracks, TRACKS_IN_PLAYLIST_REQUEST_MAX):
            tracksInPlaylistObject = self.spotipyClass.user_playlist_tracks(
                user=SPOTIFY_USERNAME, playlist_id=playlistId, limit=TRACKS_IN_PLAYLIST_REQUEST_MAX, offset=offset)
            tracksInPlaylist += tracksInPlaylistObject['items']

        return [track['track']['id'] for track in tracksInPlaylist]

    # get tracks to add
    def getTracksToAdd(self):
        trackTimeObjectsToAdd = []

        # start with only 1 track in otder to get total number in request
        response = self.spotipyClass.current_user_saved_tracks(limit=1, offset=0)
        totalNumLikedTracks = response['total']

        # request in chunks
        for offset in range(0, totalNumLikedTracks, LIKED_TRACKS_MAX):
            response = self.spotipyClass.current_user_saved_tracks(limit=LIKED_TRACKS_MAX, offset=offset)
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
    def addTracksToPlaylist(self, playlistId, trackIds):
        for offset in range(0, len(trackIds), TRACKS_TO_ADD_REQUEST_MAX):
            self.spotipyClass.user_playlist_add_tracks(
                user=SPOTIFY_USERNAME,
                playlist_id=playlistId,
                tracks=trackIds[offset:min(offset+TRACKS_TO_ADD_REQUEST_MAX, len(trackIds))])

    # map from playlist names to tracks
    def getPlaylistMapping(self, trackTimeObjects):
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
    def removeExistingTrackIds(self, existingTrackIdsInPlaylist, trackIds):
        toReturn = []

        for trackId in trackIds:
            if trackId not in existingTrackIdsInPlaylist:
                toReturn.append(trackId)

        return toReturn

    # call to initiate archive
    def archive(self):
        trackTimeObjects = self.getTracksToAdd()
        playlistToTracksMap = self.getPlaylistMapping(trackTimeObjects)

        for playlistName, trackIds in playlistToTracksMap.items():
            playlistId = self.getPlaylistToAddTo(playlistName)
            existingTrackIdsInPlaylist = set(self.getExistingTrackIdsInPlaylist(playlistId))
            trackIdsToAdd = self.removeExistingTrackIds(existingTrackIdsInPlaylist, trackIds)
            self.addTracksToPlaylist(playlistId, trackIdsToAdd)