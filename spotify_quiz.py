import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import List, Dict, Tuple
import random
from openai import OpenAI
import time
import datetime
import os

'''
To do:

hints:
    display picture of album cover
    display picture of artist
    - reduces points awarded

'''

class SpotifyQuizGame:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        # sets up spotipy, openai, and variables needed

        # init spotipy
        auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope="user-library-read user-read-playback-state user-modify-playback-state")
        self.sp = spotipy.Spotify(auth_manager=auth_manager)

        # init openai
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # init variables and flags
        self.player_name: str = ''
        
        self.playlist_name: str = ''
        self.playlist_id: str = ''
        

        self.difficulty: str = ''
        self.game_mode: str = ''
        self.number_of_rounds: int= 0
        
        self.song_count: int = 1 # keep track of how many songs have been played

        self.first_play_through: bool = True
        self.user_wants_previous_options: bool = False
        self.artist_playlist_selection: bool = False # flag so gpt knows to only give similar songs by same artist
        self.unlimited_rounds: bool = False

        self.song_play_duration: int = 15
        self.current_round_user_points: int = 0

        self.correct_answer_reward_points: int = 10
        self.second_correct_answer_reward_points: int = 5

    def get_similar_tracks(self, track_id: str) -> List[str]:
        # use gpt to find 4 similar tracks to the track passed in.
        # if user has selected an artit playlist, gpt will give songs only by the same artist
        # returns list of strings in format 'song by artist'
        try:
            track = self.sp.track(track_id)
            artist_name: str = track['artists'][0]['name']
            track_name: str = track['name']

            # using openai here because spotify deprecated song recommendation api
            # https://platform.openai.com/docs/quickstart?language=python

            if self.artist_playlist_selection == False:
                completion = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {
                            "role": "user",
                            "content": f"Generate exactly 4 songs that are similar to {track_name} by {artist_name} please. \
                            Format the songs as so: Songname by Artist. Be sure not to give the same song given. Don't add any extra text. \
                            If an artist feature is in the song title (rarely), move it to after the artist similarly to most songs \
                            Just do Song by Artist,Song by Artist,Song by Artist,Song by Artist"
                        }
                    ]
                )
            else:
                completion = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {
                            "role": "user",
                            "content": f"Generate exactly 4 songs that are similar to {track_name} by {artist_name} please. \
                            Format the songs as so: Songname by Artist. MAKE SURE THE SIMILAR SONGS ARE BY THE SAME ARTIST GIVEN. \
                            Be sure not to give the same song given. Don't add any extra text. \
                            If an artist feature is in the song title (rarely), move it to after the artist similarly to most songs \
                            Just do Song by Artist,Song by Artist,Song by Artist,Song by Artist"
                        }
                    ]
                )
            similar_songs: List[str] = completion.choices[0].message.content.split(',')
            similar_songs = [song.lstrip() for song in similar_songs]
            #print(similar_songs)
            return similar_songs
        except:
            return

    def play_audio_preview(self, track_id: str):
        # previews spotify track in browser or computer application

        track_uri: str = f"spotify:track:{track_id}"
        try:
            devices = self.sp.devices()
            if devices['devices']:
                device_id: str = devices['devices'][0]['id']
                self.sp.start_playback(device_id=device_id, uris=[track_uri])
                time.sleep(self.song_play_duration)
                self.sp.pause_playback()
        except:
            print("no active devices, please try again")
            quit()
    
    def display_game_details(self):
        print("\nThis game has you listen to a short clip of the start of a song on spotify")
        print("and it will ask you to guess for the correct song out of 5 options.\n")
        print("The 4 other options will be songs similar to the correct answer")
        print("Get the correct answer right to get points! If you get it wrong the first try")
        print("you can still get partial credit if you get it right on the seconnd try.\n")
        print("Two chances is all you get!\n")
        print("Scores are saved on a scores.txt file with the date, you name, score, difficulty, and game mode")
        print("of the game and how many rounds you played\n")
        print("Credits to spotify and the creators of the playlists used. No music played is mine\n")

    def welcome(self):
        if self.first_play_through:
            print("Welcome to Spotify Song Quiz Game")
            print("Ensure your spotify client is open and you have spotify premium!")
            print("Enter your name to keep your scores on the leaderboard:")
            self.player_name = input()
        while(1):
            print("\nSelect an option")
            print("1. Start new game")
            print("2. View high score")
            print("3. Read game details")
            print("4. Quit")

            first_selection: str = input()

            if first_selection == '1':
                return
            elif first_selection == '2':
                self.view_high_score()
            elif first_selection == '3':
                self.display_game_details()
            elif first_selection == '4':
                print("Goodbye!")
                exit()
            else:
                print("Please input valid option")
    
    def select_difficulty(self):
        # user selects difficulty to play on in the next game (how long song is previewed)
        print("\nSelect a difficulty:")
        while(1):
            print("1. Easy (15 second song preview)")
            print("2. Medium (10 second song preview)")
            print("3. Hard (5 second song preview)")
            print("4. Extreme (1 second song preview)")
            
            game_mode_selection: str = input()
            if game_mode_selection == '1':
                self.difficulty = 'easy'
                self.correct_answer_reward_points = 2
                self.second_correct_answer_reward_points = 1
                self.song_play_duration = 15
                return
            elif game_mode_selection == '2':
                self.difficulty = 'medium'
                self.correct_answer_reward_points = 4
                self.second_correct_answer_reward_points = 2
                self.song_play_duration = 10
                return
            elif game_mode_selection == '3':
                self.difficulty = 'hard'
                self.correct_answer_reward_points = 10
                self.second_correct_answer_reward_points = 5
                self.song_play_duration = 5
                return
            elif game_mode_selection == '4':
                self.difficulty = 'extreme'
                self.correct_answer_reward_points = 20
                self.second_correct_answer_reward_points = 10
                self.song_play_duration = 1
                return
            else:
                print("Please input a valid option")
    
    def select_game_mode(self):
        # user selects game mode (how many songs they will be quizzed over in the next game)
        print("\nSelect duration of game:")
        while(1):
            print("1. Short (3 songs)")
            print("2. Medium (5 songs)")
            print("3. Long (10 songs)")
            print("4. Unlimited (until you want to stop)")

            number_of_rounds_selection = input()

            if number_of_rounds_selection == '1':
                self.number_of_rounds = 3
                self.game_mode = 'short'
                return
            elif number_of_rounds_selection == '2':
                self.number_of_rounds = 5
                self.game_mode = 'medium'
                return
            elif number_of_rounds_selection == '3':
                self.number_of_rounds = 10
                self.game_mode = 'long'
                return
            elif number_of_rounds_selection == '4':
                self.unlimited_rounds = True
                self.game_mode = 'unlimited'
                return
            else:
                print("Please input valid option!")
    
    def get_tracks_from_playlist(self) -> List[Dict]:
        return self.sp.playlist_tracks(self.playlist_id)

    def get_top_hundred_playlist_id(self):
        # https://open.spotify.com/playlist/5ABHKGoOzxkaa28ttQV9sE?si=94ea1ccdd0e24c02
        return '5ABHKGoOzxkaa28ttQV9sE'

    def get_user_inputted_id(self) -> str:
        # check if user inputted a valid playlist then return playlist id
        while(1):
            try:
                print("Input playlist url or input back to go back. has to look something like: https://open.spotify.com/playlist/******=******* Cannot be playlist created by spotify")
                user_inputted_url: str = input()
                if user_inputted_url == 'back':
                    self.playlist_selection()
                    break

                # extract only id. its the string after 'playlist/' and before '?si'
                user_inputted_url_split: str = user_inputted_url.split('/')
                playlist_id: str = user_inputted_url_split[4].rsplit('?')[0]
                test = self.sp.playlist_tracks(playlist_id) # error will arrise if this fails
                return playlist_id

            except 404:
                print("Error. Invalid playlist inputted")
        
    def get_specific_genre_playlist_id(self) -> str:
        # ask user to select from genres and return playlist id for genre playlist

        genre_playlists: dict = {
            'classic rock': '1ti3v0lLrJ4KhSTuxt4loZ', # https://open.spotify.com/playlist/1ti3v0lLrJ4KhSTuxt4loZ?si=8771d5a7b1854847
            'hip hop': '62y3BHKehWnb1hlaPclDAA', # https://open.spotify.com/playlist/62y3BHKehWnb1hlaPclDAA?si=6db770b3d5f54011
            'rap': '01MRi9jFGeSEEttKOk7VgR', # https://open.spotify.com/playlist/01MRi9jFGeSEEttKOk7VgR?si=ad4829e74ccc4341
            'country': '02t75h5hsNOw4VlC1Qad9Z', # https://open.spotify.com/playlist/02t75h5hsNOw4VlC1Qad9Z?si=d5f0b896f15347cf
            'pop': '6mtYuOxzl58vSGnEDtZ9uB', # https://open.spotify.com/playlist/6mtYuOxzl58vSGnEDtZ9uB?si=14c9582de50440c0
            'classical': '27Zm1P410dPfedsdoO9fqm' # https://open.spotify.com/playlist/27Zm1P410dPfedsdoO9fqm?si=af0832c6a8714739
        }

        print("Input a genre from the following options, or say back to go back")

        while(1):
            print("Classic Rock, Hip hop, Rap, Country, Pop, Classical")
            genre_pick: str = input()
            if genre_pick in genre_playlists:
                return genre_playlists[genre_pick]
            elif genre_pick == 'back':
                self.playlist_selection()
                break
            else:
                print("Please input valid option")

    def get_specific_artist_playlist_id(self) -> str:
        # ask user to select an artist and return playlist id for artist playlist

        artist_playlists: dict = {
            'elvis presley': '0WJ02LEK0YbWKiynx2YQQZ', # https://open.spotify.com/playlist/0WJ02LEK0YbWKiynx2YQQZ?si=efde2afb19174976
            'michael jackson': '4xZkkngX0R5HsNhm4BpeGT', # https://open.spotify.com/playlist/4xZkkngX0R5HsNhm4BpeGT?si=ef3cc1243e744745
            'the rolling stones': '6gV6RlpjRDCbVB7z0M0b0p', # https://open.spotify.com/playlist/6gV6RlpjRDCbVB7z0M0b0p?si=5e72d395840d4d39
            'elton john': '0ydfO36a9Dexg2voPXhhNS', # https://open.spotify.com/playlist/0ydfO36a9Dexg2voPXhhNS?si=defe7e3eee2a4744
            'adele': '09p59sPpHqIJ5dZ8kwb66S', # https://open.spotify.com/playlist/09p59sPpHqIJ5dZ8kwb66S?si=079134693c434129
            'drake': '6SFx39GsC05tDIFlTMUsIK', # https://open.spotify.com/playlist/6SFx39GsC05tDIFlTMUsIK?si=bc4606671e25417d
            'the weeknd': '1kIlqM7lAP9vDZtW2Pchhb', # https://open.spotify.com/playlist/1kIlqM7lAP9vDZtW2Pchhb?si=c1ccf95cd4cc454e
            'kendrick lamar': '5lBSVt2KMhM5EdSm6WSxpg', # https://open.spotify.com/playlist/5lBSVt2KMhM5EdSm6WSxpg?si=d44f68a205604cf9
            'playboi carti': '7dRabwP32H3bBtPxr98uDg' # https://open.spotify.com/playlist/7dRabwP32H3bBtPxr98uDg?si=ab6d4ec07f5648ee
        }

        print("Input an artist from the following options, or input back to go back")
        while(1):
            print("Elvis Presley, Michael Jackson, The Rolling Stones, Elton John, Adele, Drake, The Weeknd, Kendrick Lamar, Playboi Carti")
            artist_pick: str = input().strip().lower()
            if artist_pick in artist_playlists:
                return artist_playlists[artist_pick]
            elif artist_pick == 'back':
                self.playlist_selection()
                break
            else:
                print("Please input valid option")

    def get_specific_time_period_playlist_id(self) -> str:
        # ask user to select a time period and return playlist id for said time period playlist

        time_period_playlists: dict = {
            '2020s': '2fmTTbBkXi8pewbUvG3CeZ', # https://open.spotify.com/playlist/2fmTTbBkXi8pewbUvG3CeZ?si=6f5c007c95ac4d8e
            '2010s': '357fWKFTiDhpt9C69CMG4q', # https://open.spotify.com/playlist/357fWKFTiDhpt9C69CMG4q?si=3f07ea96f3c34f34
            '2000s': '4TvVpoyxF9kmnu1GLikiQp', # https://open.spotify.com/playlist/4TvVpoyxF9kmnu1GLikiQp?si=0f175a9e463e438b
            '1990s': '409KR0gW2jbhkN4vJ8QqUl', # https://open.spotify.com/playlist/409KR0gW2jbhkN4vJ8QqUl?si=03da4bb4808e4948
            '1980s': '2y09fNnXHvoqc1WGHvbhkZ', # https://open.spotify.com/playlist/2y09fNnXHvoqc1WGHvbhkZ?si=832f69ca2f9b47e6
            '1970s': '7e6gKFwEXMF6uDQzmD9YXn', # https://open.spotify.com/playlist/7e6gKFwEXMF6uDQzmD9YXn?si=e7aa821197cd4f95
            '1960s': '4ZuX2YvKAlym0a8VozqV1U', # https://open.spotify.com/playlist/4ZuX2YvKAlym0a8VozqV1U?si=543be33764a943a4
            '1950s': '0VdElawgQD0z0faqcVfULC'  # https://open.spotify.com/playlist/0VdElawgQD0z0faqcVfULC?si=b604f55eff854460
        }
        print("Input a time period as so from the following options, or input back to go back")
        while(1):
            print("2020s, 2010s, 2000s, 1990s, 1980s, 1970s, 1960s, 1950s")
            time_period_pick: str = input().strip().lower()
            if time_period_pick in time_period_playlists:
                return time_period_playlists[time_period_pick]
            elif time_period_pick == 'back':
                self.playlist_selection()
                break
            else:
                print("Please input valid option")

    def playlist_selection(self):
        # user selects what type of playlist they want to be quizzed over in the next game
        # or if they want to input own playlist
        while(1):
            print("\nTo start a game, first select a pre-inputted playlist or input your own:")
            print("1. Top 100 Streamed Songs of All Time")
            print("2. Select a genre")
            print("3. Select an artist")
            print("4. Select a time period (2010s, 2000s, 1990s, etc)")
            print("5. Input own playlist")
            playlist_choice_selection: str = input()

            if playlist_choice_selection == '1':
                self.playlist_id = self.get_top_hundred_playlist_id()
                self.playlist_name = self.sp.user_playlist(user=None, playlist_id=self.playlist_id)['name']
                break
            elif playlist_choice_selection == '2':
                self.playlist_id = self.get_specific_genre_playlist_id()
                self.playlist_name = self.sp.user_playlist(user=None, playlist_id=self.playlist_id)['name']
                break
            elif playlist_choice_selection == '3':
                self.playlist_id = self.get_specific_artist_playlist_id()
                self.playlist_name = self.sp.user_playlist(user=None, playlist_id=self.playlist_id)['name']
                self.artist_playlist_selection = True
                break
            elif playlist_choice_selection == '4':
                self.playlist_id = self.get_specific_time_period_playlist_id()
                self.playlist_name = self.sp.user_playlist(user=None, playlist_id=self.playlist_id)['name']
                break
            elif playlist_choice_selection == '5':
                self.playlist_id = self.get_user_inputted_id()
                self.playlist_name = self.sp.user_playlist(user=None, playlist_id=self.playlist_id)['name']
                break
            else:
                print("Please input valid option")
    
    def view_high_score(self):
        # views highest score achieved in quiz game in scores.txt
        with open('scores.txt', 'r') as file:
            try:
                high_score: int = 0
                high_score_details: List = list()
                for line in file:
                    #print(line)

                    score_details = line.strip().split(":")
                    if len(score_details) != 6:
                        continue

                    date, name, points, game_mode, difficulty, playlist_name = score_details

                    if int(points) > high_score:
                        high_score = int(points)
                        high_score_details = [date, name, points, game_mode, difficulty, playlist_name]

                if high_score_details:
                    print(f"\nThe current high score is {high_score} points by {high_score_details[1]} on {high_score_details[3]} difficulty on {high_score_details[4]} mode on the playlist '{high_score_details[5]}'")
                    print(f"Scored on {high_score_details[0]}\n")
                    
            except FileNotFoundError:
                print("No scores have been tracked yet!\n")

    def add_score_to_scoreboard(self):
        with open('scores.txt', 'a') as file:
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime("%m/%d/%Y") # xx/xx/xxxx
            user_score = f"{formatted_datetime}:{self.player_name}:{self.current_round_user_points}:{self.game_mode}:{self.difficulty}:{self.playlist_name}\n"

            file.write(user_score)


    def play_round(self, tracks: List[Dict]):
        # plays the round of song quiz from given playlist tracks
        # will play through the entire match and adjusts variables as needed

        track: dict = tracks.pop()
        track_id: str = track['track']['id']

        correct_song: str = track['track']['name']
        correct_artist: str = track['track']['artists'][0]['name']

        similar_tracks: List[str] = self.get_similar_tracks(track['track']['id'])
        
        quiz_tracks = list()
        for track in similar_tracks:
            quiz_tracks.append(track)

        quiz_tracks.append(f"{correct_song} by {correct_artist}")
        random.shuffle(quiz_tracks)

        print(f"\nPlaying song number {self.song_count}!")
        self.play_audio_preview(track_id)
        print("Select the correct song: ")
        
        correct_idx = 0
        for idx in range(len(quiz_tracks)):            
            print(f"{idx + 1}: {quiz_tracks[idx]}")

            # get correct song index to compare to users answer later
            current_song = quiz_tracks[idx].split('by')[0]
            if correct_song.strip().lower() == current_song.strip().lower():
                correct_idx = idx + 1
        
        answer = int(input())

        if answer != correct_idx:
            print("\nIncorrect! Try again")
            for idx in range(len(quiz_tracks)):            
                print(f"{idx + 1}: {quiz_tracks[idx]}")
            answer = int(input())
            # second guess
            if answer == correct_idx:
                print(f"Correct! You earned {self.second_correct_answer_reward_points} points for guessing it on second try")
                self.current_round_user_points += self.second_correct_answer_reward_points
            else:
                print("Incorrect! You ran out of tries")
        else:
            print(f"\nCorrect! You earned {self.correct_answer_reward_points} points")
            self.current_round_user_points += self.correct_answer_reward_points
        if self.unlimited_rounds:
            print(f"You currently have {self.current_round_user_points} points")
        
    def after_game_selection(self):
        # selection for user to make after the round has ended

        print("\nThanks for playing! Select an option:")
        while(1):
            print("1. Play again with previous settings and playlist")
            print("2. Play again (restart selections)")
            print("3. View high score")
            print("4. Quit")

            after_game_selection: str = input()

            if after_game_selection == '1':
                self.user_wants_previous_options = True
                self.song_count = 1
                self.current_round_user_points = 0
                self.play_game()
            elif after_game_selection == '2':
                self.user_wants_previous_options = False
                self.unlimited_rounds = False
                self.artist_playlist_selection = False
                self.song_count = 1
                self.current_round_user_points = 0
                self.play_game()
            elif after_game_selection == '3':
                self.view_high_score()
            elif after_game_selection == '4':
                print("Goodbye!")
                quit()
            else:
                print("Please input valid option")


    def play_game(self):
        # handles inputs needed before round starts
        # handles things after round ends
        # handles unlimited game mode

        if self.first_play_through:
            self.welcome()
        
        if self.user_wants_previous_options == False:
            self.select_difficulty()
            self.select_game_mode()
            self.playlist_selection()
    
        # player has selected to start a game
        
        tracks: List[dict] = self.get_tracks_from_playlist()['items']
        random.shuffle(tracks)

        # only so it doesn't say 1 seconds on extreme mode
        if self.difficulty == 'extreme':
            second_count_string = 'second'
        else:
            second_count_string = 'seconds'

        print(f"\nStarting game with {self.number_of_rounds} rounds with song duration of {self.song_play_duration} {second_count_string} on the playlist '{self.playlist_name}'!\nGood luck!\n")
        
        if not self.unlimited_rounds:
            for _ in range(self.number_of_rounds):
                self.play_round(tracks)
                self.song_count += 1
        else:
            while(1):
                self.play_round(tracks)
                self.song_count += 1
                
                print("Enter 1 to continue playing. Enter 2 to quit.")
                user_continue_selection = input()
                if user_continue_selection == '1':
                    continue
                elif user_continue_selection == '2':
                    break
                else:
                    print("Please input valid option")
            
        print(f"You ended with a final score of {self.current_round_user_points} points!!!")

        self.first_play_through = False
        self.add_score_to_scoreboard()
        self.after_game_selection()

def main():
    CLIENT_ID = ""
    CLIENT_SECRET = ""

    REDIRECT_URI = 'http://localhost:8888/callback'
    
    new_game = SpotifyQuizGame(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI)
    new_game.play_game()

if __name__ == "__main__":
    main()