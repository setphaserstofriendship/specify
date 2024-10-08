import os
import configparser
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from functions import (
    display_banner,
    get_top_tracks,
    get_liked_songs,
    get_random_seed_tracks,
    get_recommendations,
    filter_tracks_by_tempo,
    get_all_playlist_tracks,
    create_playlist,
    add_tracks_to_playlist
)

# Define the path to the config file in the user's home directory
config_file_path = os.path.expanduser("~/.config/specify/specify.conf")

# Check if the config file exists
if not os.path.exists(config_file_path):
    print(f"Config file not found at {config_file_path}. Please use the template config found in the repo and fill "
          f"out your Spotify credentials.")
    exit(1)

# Read from the .conf file
config = configparser.ConfigParser()
config.read(config_file_path)

# Spotify API credentials
CLIENT_ID = config.get('spotify', 'client_id', fallback=os.getenv('SPOTIPY_CLIENT_ID'))
CLIENT_SECRET = config.get('spotify', 'client_secret', fallback=os.getenv('SPOTIPY_CLIENT_SECRET'))
REDIRECT_URI = config.get('spotify', 'redirect_uri', fallback="http://localhost:8888/callback")
SCOPE = config.get('spotify', 'scope', fallback="user-library-read playlist-modify-public user-top-read")

# Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=SCOPE))


# Main function
def main():
    display_banner()

    # Read values from the config file or ask the user if missing
    try:
        target_tempo = int(config.get('playlist_settings', 'target_tempo'))
    except (configparser.NoOptionError, ValueError):
        target_tempo = int(input("Enter desired tempo (bpm): "))

    try:
        tempo_tolerance = int(config.get('playlist_settings', 'tempo_tolerance'))
    except (configparser.NoOptionError, ValueError):
        tempo_tolerance = int(input("Specify +- bpm tolerance (low tolerance may lead to a short playlist): "))

    try:
        playlist_length = int(config.get('playlist_settings', 'playlist_length'))
    except (configparser.NoOptionError, ValueError):
        playlist_length = int(input("Minimum playlist length (no. of tracks): "))

    try:
        exclude_existing_tracks = config.getboolean('playlist_settings', 'exclude_existing_tracks')
    except (configparser.NoOptionError, ValueError):
        exclude_existing_tracks = input(
            "Should the playlist exclude tracks already present in your other playlists? (y/n): ").strip().lower() == 'y'

    try:
        seed_source = config.get('playlist_settings', 'seed_source')
    except configparser.NoOptionError:
        seed_source = input("Seed playlist with (1) Top tracks or (2) Liked songs? Enter 1 or 2: ").strip()

    user_id = sp.current_user()['id']

    # Get all tracks from all user's playlists if necessary
    all_user_tracks = set()
    if exclude_existing_tracks:
        all_user_tracks = get_all_playlist_tracks(sp, user_id)

    # Get seed tracks based on user choice
    seed_tracks = []
    if seed_source == '1':
        top_tracks = get_top_tracks(sp)
        seed_tracks = [track['id'] for track in top_tracks[:5]]  # Use top tracks as seeds
    elif seed_source == '2':
        liked_tracks = get_liked_songs(sp, limit=50)  # Fetch liked songs (limit to 100 for performance)
        seed_tracks = [track['id'] for track in
                       get_random_seed_tracks(liked_tracks, seed_count=5)]  # Randomly select 5 liked songs

    # Get recommended tracks and filter by tempo
    filtered_tracks = []
    all_tempos = []  # To store the tempos of all filtered tracks
    while len(filtered_tracks) < playlist_length:
        recommended_tracks = get_recommendations(sp, seed_tracks=seed_tracks, limit=100)
        new_filtered_tracks, new_tempos = filter_tracks_by_tempo(sp, recommended_tracks, target_tempo,
                                                                 tempo_tolerance)

        # Add only new tracks to avoid duplicates and existing user tracks if needed
        new_filtered_tracks_ids = {track['id'] for track in new_filtered_tracks}
        existing_filtered_tracks_ids = {track['id'] for track in filtered_tracks}
        if exclude_existing_tracks:
            unique_new_tracks = [track for track in new_filtered_tracks if
                                 track['id'] not in existing_filtered_tracks_ids and track[
                                     'id'] not in all_user_tracks]
        else:
            unique_new_tracks = [track for track in new_filtered_tracks if
                                 track['id'] not in existing_filtered_tracks_ids]

        filtered_tracks.extend(unique_new_tracks)
        all_tempos.extend(new_tempos)  # Store the tempos

        # Print the progress
        print(f"{len(filtered_tracks)} out of {playlist_length} tracks collected.")

        # Check if we have enough unique recommendations to proceed
        if len(recommended_tracks) < 100:
            break

    # Ensure there are enough tracks to create a playlist
    if len(filtered_tracks) < playlist_length:
        print("Not enough tracks. Try increasing tempo tolerance and/or reducing playlist length.")
        return

    # Calculate lowest and highest tempo
    if all_tempos:
        lowest_bpm = min(all_tempos)
        highest_bpm = max(all_tempos)
        # Create the playlist description with BPM info
        playlist_description = f"{lowest_bpm:.2f}-{highest_bpm:.2f}"
        print("Playlist description:", playlist_description)  # Print description to console
    else:
        print("No tracks found with the specified tempo range.")
        return

    # Create a new playlist
    playlist_name = input("Playlist name: ")
    playlist_id = create_playlist(sp, user_id, playlist_name, playlist_description)

    # Add tracks to the new playlist
    add_tracks_to_playlist(sp, playlist_id, filtered_tracks)
    print(f"Playlist '{playlist_name}' created with {len(filtered_tracks)} tracks.")


if __name__ == "__main__":
    main()
