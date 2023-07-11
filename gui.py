import json
import os
import sys
import webbrowser
from threading import Thread

import requests
import spotipy
from PyQt6 import uic
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication, QWidget, QTableWidgetItem
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


def detect_folder():
    if os.path.isfile("C:\Program Files (x86)\Steam\steamapps\common\Beat Saber/Beat Saber.exe"):
        return "C:\Program Files (x86)\Steam\steamapps\common\Beat Saber"
    elif os.path.isfile("C:\Program Files\Oculus\Software\Software\hyperbolic-magnetism-beat-saber\/Beat Saber.exe"):
        return "C:\Program Files\Oculus\Software\Software\hyperbolic-magnetism-beat-saber"
    else:
        print("Couldn't detect automatically the beat saber folder")


class Beatify(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi("first.ui", self)

        self.warning.hide()
        self.displaySongs.setHorizontalHeaderLabels(
            ["Playlist", "Status", "Artist", "Spotify Name", "BeatSaver Name", "BeatSaver ID"])
        print("Successfully loaded UI")
        self.installDir.setText(detect_folder())

        self.startConverting.clicked.connect(self.convert_playlist)
        self.urlInput.editingFinished.connect(self.fetch_playlist_infos)
        self.savePlaylist.clicked.connect(self.save_playlist)
        self.displaySongs.cellClicked.connect(self.toggl_playlist)

    def fetch_playlist_infos(self):
        try:
            results = spotify.playlist(self.urlInput.text())

            self.displayPlaylistInfo.setText(
                f"Playlist {results['name']} by {results['owner']['display_name']} with {results['tracks']['total']} songs"
            )

            self.playlistDescription.setText(results['description'])
            self.playlistName.setText(results['name'])
            self.playlistAuthor.setText(results['owner']['display_name'])

            if results['tracks']['total'] > 100:
                self.warning.show()
            else:
                self.warning.hide()

        except spotipy.exceptions.SpotifyException:
            self.displayPlaylistInfo.setText("URL is not a valid Spotify Playlist URL")
            self.warning.hide()

    def convert_playlist(self):
        print("Converting Playlist...")
        song_url = self.urlInput.text()
        self.displaySongs.setRowCount(0)
        self.savePlaylist.setEnabled(False)

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
        self.savePlaylist.setEnabled(True)

    def save_playlist(self):
        print("Saving Playlist...")
        self.savePlaylist.setEnabled(False)
        self.status.setText("Saving Playlist...")

        playlist_name = self.playlistName.text()
        playlist_description = self.playlistDescription.text()
        beatsaber_folder = self.installDir.text()

        playlist['playlistTitle'] = playlist_name
        playlist['playlistDescription'] = playlist_description

        for song in song_list:
            row, column = self.search_table(song['key'])
            background_color = self.displaySongs.item(row, 0).background().color()

            if background_color == QColor("green"):
                if song['key'] == self.displaySongs.item(row, 5).text():
                    playlist['songs'].append(song)
            else:
                print(f"Song {song['key']} is not green")

        print(playlist)
        playlist_name = playlist_name.replace(" ", "_")
        playlist_json = json.dumps(playlist)

        if os.path.isfile(beatsaber_folder + "/Beat Saber.exe"):
            print("Found Beat Saber Folder")
            playlist_file = open(f"{beatsaber_folder}/Playlists/{playlist_name}.json", "w")
            playlist_file.write(playlist_json)
        else:
            self.status.setText("Beat Saber Folder not found")
            print("The Folder does not seem to be the Beat Saber installation folder")

        self.status.setText("Saved Playlist")
        self.savePlaylist.setEnabled(True)
        print(f"Saved Playlist to {beatsaber_folder}/Playlists/{playlist_name}.json")

    def search_table(self, search_text):
        for row in range(self.displaySongs.rowCount()):
            for column in range(self.displaySongs.columnCount()):
                item = self.displaySongs.item(row, column)
                if item and search_text in item.text():
                    return row, column

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

        print("Sending request to BeatSaver")
        response = requests.get("https://api.beatsaver.com/search/text/0", parameters)
        print(response.status_code)
        if response.status_code != 200:
            while response.status_code == 504:
                response = requests.get("https://api.beatsaver.com/search/text/0", parameters)
            else:
                return

        sorted_songs = []
        json_response_array = json.loads(response.text)
        json_response_array = json_response_array["docs"]
        json_response_current_number = 0

        while len(json_response_array) > json_response_current_number:
            json_response = json_response_array[json_response_current_number]

            # if (fuzz.ratio(song_name.lower(), json_response["name"].lower())) < 80:
            if song_name.lower() not in json_response["name"].lower():
                print(
                    f"Not the same title. The Title of the BeatSaver song is: {str(json_response['name'])}")

            else:
                song_id = json_response["id"]
                song_beatsaver_name = json_response["name"]
                song_hash = json_response["versions"][0]["hash"]
                json_response = json_response["metadata"]

                if json_response["duration"] in range(duration - 10, duration + 10):
                    print(
                        str(f"Found a song with the id: {song_id} and the name {json_response['songName']} the URL is: https://beatsaver.com/maps/{song_id}")
                    )

                    song_par = {"key": song_id, "hash": song_hash}
                    song_list.insert(len(song_list), song_par)

                    print(song_list)
                    self.displaySongs.insertRow(self.displaySongs.rowCount())
                    self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 0, QTableWidgetItem(""))
                    self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 1, QTableWidgetItem("Found a BeatMap"))
                    self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 2, QTableWidgetItem(song_artist))
                    self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 3, QTableWidgetItem(song_name))
                    self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 4,
                                              QTableWidgetItem(song_beatsaver_name))
                    self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 5, QTableWidgetItem(song_id))
                    self.displaySongs.item(self.displaySongs.rowCount() - 1, 0).setBackground(QColor("green"))
                    self.displaySongs.item(self.displaySongs.rowCount() - 1, 1).setBackground(QColor("light green"))
                    self.displaySongs.resizeColumnsToContents()

                    return

                else:
                    song_par = {"key": song_id, "hash": song_hash, "duration": json_response["duration"],
                                "name": json_response["songName"]}
                    sorted_songs.insert(len(song_list), song_par)
                    print("A song was found, but probably not match the one from Spotify.")
                    print(f"Spotify: {song_name} with the duration of {duration}s.")
                    print(
                        f"Beatsaver: {json_response['songName']} with the duration of {json_response['duration']}s and the URL is: https://beatsaver.com/maps/{song_id}"
                    )
            json_response_current_number = json_response_current_number + 1

        self.displaySongs.insertRow(self.displaySongs.rowCount())
        self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 0, QTableWidgetItem(""))

        if len(sorted_songs) > 0:
            song_par = {"key": sorted_songs[0]['key'], "hash": sorted_songs[0]['hash']}
            song_list.insert(len(song_list), song_par)

            self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 1,
                                      QTableWidgetItem("Found probably no Beatmap"))
            self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 4, QTableWidgetItem(sorted_songs[0]["name"]))
            self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 5, QTableWidgetItem(sorted_songs[0]["key"]))
            self.displaySongs.item(self.displaySongs.rowCount() - 1, 1).setBackground(QColor("#ffff80"))
        else:
            # song_par = {"key": "", "hash": ""}
            # song_list.insert(len(song_list), song_par)
            self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 1,
                                      QTableWidgetItem("Found no Beatmap"))
            self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 4, QTableWidgetItem(""))
            self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 5, QTableWidgetItem(""))
            self.displaySongs.item(self.displaySongs.rowCount() - 1, 1).setBackground(QColor("#ff474c"))

        self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 2, QTableWidgetItem(song_artist))
        self.displaySongs.setItem(self.displaySongs.rowCount() - 1, 3, QTableWidgetItem(song_name))
        self.displaySongs.item(self.displaySongs.rowCount() - 1, 0).setBackground(QColor("red"))
        self.displaySongs.resizeColumnsToContents()

    def toggl_playlist(self, row, column):
        if column == 0:
            current_color = self.displaySongs.item(row, column).background().color()

            if current_color == QColor("red"):
                new_color = QColor("green")
            else:
                new_color = QColor("red")

            self.displaySongs.item(row, column).setBackground(new_color)
        elif column == 5:
            print("Opening BeatSaver")
            webbrowser.open("https://beatsaver.com/maps/" + self.displaySongs.item(row, column).text())


app = QApplication([])

window = Beatify()
window.show()

sys.exit(app.exec())
