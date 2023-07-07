import requests
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

file = open("./credentials.json", "r")
credentials = json.load(file)

song_input = input("Song or Playlist URL: ")
playlist_name = input("Playlist name: ")

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id=credentials["SPOTIPY_CLIENT_ID"],
    client_secret=credentials["SPOTIPY_CLIENT_SECRET"]))

playlist = {
    "playlistTitle": playlist_name,
    "playlistAuthor": "Beatify",
    "playlistDescription": "A Playlist created with Beatify",
    "songs": []
}
song_list = []


def song_infos(data):
    song_name = data["name"]
    song_artist = data["artists"][0]["name"]
    song_duration = int(data["duration_ms"] / 1000)
    print(song_name + " by " + song_artist + " with the duration of " + str(song_duration) + "s")
    search_song(song_name, song_artist,  song_duration)


def search_song(song_name, song_artist, duration):
    parameters = {
        "q": song_name, # + "+" + song_artist,
        "sortOrder": "Relevance"
    }

    response = requests.get("https://api.beatsaver.com/search/text/0", parameters)
    print(response.url)
    if response.status_code == 200:
        json_response_array = json.loads(response.text)
        json_response_array = json_response_array["docs"]
        json_response_current_number = 0
        while len(json_response_array) > json_response_current_number:
            json_response = json_response_array[json_response_current_number]
            if song_name.lower() not in json_response["name"].lower():
                print("No the same title. The Title of the song is: " + json_response["name"])
            else:
                song_id = json_response["id"]
                song_hash = json_response["versions"][0]["hash"]
                json_response = json_response["metadata"]
                if json_response["duration"] in range(duration - 10, duration + 10):
                    print(f"Found a song with the id: {song_id} and the name " + json_response["songName"] + " the URL is: https://beatsaver.com/maps/" + song_id)
                    print("The hash is: " + song_hash)
                    song_par = {"key": song_id, "hash": song_hash}
                    song_list.insert(len(song_list), song_par)
                    playlist["songs"] = song_list
                    return

                else:
                    print("A song was found, but may not match the one from Spotify.")
                    print("Spotify: " + song_name + " with the duration of " + str(duration) + "s" " and the URL is: https://beatsaver.com/maps/" + song_id)
                    print("Beatsaver: " + json_response["songName"] + " with the duration of " + str(
                        json_response["duration"]) + "s")
            json_response_current_number = json_response_current_number + 1


def get_song(song_id):
    if 'playlist' in song_id:
        results = spotify.playlist_items(song_id, limit=None)
        results = results['items']
        i = 0
        while i < len(results):
            print(i)
            results_track = results[i]['track']
            song_infos(results_track)
            i = i + 1

        playlist_json = json.dumps(playlist)
        print(playlist_json)
        file = open("./beatsaver2.json", "w")
        file.write(playlist_json)
    else:
        results = spotify.track(song_id)
        song_infos(results)
        file = open("./beatsaver2.json", "w")
        file.write(str(playlist))


get_song(song_input)
