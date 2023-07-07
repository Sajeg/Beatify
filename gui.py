import sys
from threading import Thread
import requests
from PyQt6.QtWidgets import QApplication, QWidget, QLineEdit, QPushButton, QLabel, QGridLayout, QMessageBox, \
    QVBoxLayout, QTextEdit, QListWidget, QTableWidget, QTableWidgetItem
from PyQt6 import uic
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

file = open("./credentials.json", "r")
credentials = json.load(file)

spotify = spotipy.Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id=credentials["SPOTIPY_CLIENT_ID"],
    client_secret=credentials["SPOTIPY_CLIENT_SECRET"]))

playlist = {
    "playlistTitle": "My Playlist",
    "playlistAuthor": "Beatify",
    "playlistDescription": "A Playlist created with Beatify",
    "songs": []
}

song_list = []


class Beatify(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("first.ui", self)
        print("Successfully loaded UI")
        self.startConverting.clicked.connect(self.convert_playlist)
        self.urlInput.editingFinished.connect(self.fetch_playlist_infos)

    def fetch_playlist_infos(self):
        try:
            results = spotify.playlist(self.urlInput.text())
            self.displayPlaylistInfo.setText(
                "Playlist " + results['name'] + " by " + results['owner']['display_name'] + " with " + str(
                    results['tracks']['total']) + " songs")
        except spotipy.exceptions.SpotifyException:
            self.displayPlaylistInfo.setText("URL is not valid")

    def convert_playlist(self):
        print("Converting Playlist...")
        song_url = self.urlInput.text()
        self.displaySongs.setRowCount(0)
        try:
            results = spotify.playlist_items(song_url)
            Thread(target=self.process_songs, args=[results]).start()
            print("Started Thread")
        except spotipy.exceptions.SpotifyException:
            print("URL is not a valid Spotify Playlist URL")
            return

    def process_songs(self, results):
        results = results['items']
        i = 0
        while i < len(results):
            print(str(i))
            results_track = results[i]['track']
            self.scrap_song_infos(data=results_track)
            i = i + 1

        print("Finished converting Playlist")
        playlist_json = json.dumps(playlist)
        print(str(playlist_json))
        file = open("./tmp.json", "w")
        file.write(playlist_json)
        print("Saved Playlist to tmp.json")

    def scrap_song_infos(self, data):
        song_name = data["name"]
        song_artist = data["artists"][0]["name"]
        song_duration = int(data["duration_ms"] / 1000)
        print(str(song_name + " by " + song_artist + " with the duration of " + str(song_duration) + "s"))
        self.search_song(song_name, song_artist, song_duration)

    def search_song(self, song_name, song_artist, duration):
        parameters = {
            "q": song_name,  # + "+" + song_artist,
            "sortOrder": "Relevance"
        }

        response = requests.get("https://api.beatsaver.com/search/text/0", parameters)
        print(str(response.url))
        if response.status_code == 200:
            json_response_array = json.loads(response.text)
            json_response_array = json_response_array["docs"]
            json_response_current_number = 0
            while len(json_response_array) > json_response_current_number:
                json_response = json_response_array[json_response_current_number]
                if song_name.lower() not in json_response["name"].lower():
                    print("No the same title. The Title of the song is: " + str(json_response["name"]))
                else:
                    song_id = json_response["id"]
                    song_beatsaver_name = json_response["name"]
                    song_hash = json_response["versions"][0]["hash"]
                    json_response = json_response["metadata"]
                    if json_response["duration"] in range(duration - 10, duration + 10):
                        print(str(f"Found a song with the id: {song_id} and the name " + json_response[
                            "songName"] + " the URL is: https://beatsaver.com/maps/" + song_id))
                        print(str("The hash is: " + song_hash))
                        song_par = {"key": song_id, "hash": song_hash}
                        song_list.insert(len(song_list), song_par)
                        playlist["songs"] = song_list

                        self.displaySongs.insertRow(self.displaySongs.rowCount())
                        self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 0, QTableWidgetItem("Found a Beatmap"))
                        self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 1, QTableWidgetItem(song_artist))
                        self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 2, QTableWidgetItem(song_name))
                        self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 3, QTableWidgetItem(song_beatsaver_name))
                        self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 4, QTableWidgetItem(song_id))

                        return

                    else:
                        print("A song was found, but probably not match the one from Spotify.")
                        print("Spotify: " + song_name + " with the duration of " + str(
                            duration) + "s" " and the URL is: https://beatsaver.com/maps/" + song_id)
                        print("Beatsaver: " + json_response["songName"] + " with the duration of " + str(
                            json_response["duration"]) + "s")
                json_response_current_number = json_response_current_number + 1

            self.displaySongs.insertRow(self.displaySongs.rowCount())
            self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 0, QTableWidgetItem("Found no Beatmap"))
            self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 1, QTableWidgetItem(song_artist))
            self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 2, QTableWidgetItem(song_name))


app = QApplication([])
# app = QApplication(sys.argv)

window = Beatify()
window.show()

sys.exit(app.exec())
