import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Spotify API credentials
CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
REDIRECT_URI = "http://localhost:8888/callback"
SCOPE = "user-library-read playlist-modify-public user-top-read"

# Authenticate with Spotify
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CLIENT_ID,
                                               client_secret=CLIENT_SECRET,
                                               redirect_uri=REDIRECT_URI,
                                               scope=SCOPE))


def display_banner():
    banner = r"""
      ____                  _  __       
     / ___| _ __   ___  ___(_)/ _|_   _ 
     \___ \| '_ \ / _ \/ __| | |_| | | |
      ___) | |_) |  __/ (__| |  _| |_| |
     |____/| .__/ \___|\___|_|_|  \__, |
           |_|                    |___/ 

        """
    print(banner)
    print("Generate customized Spotify playlists.")


def get_top_tracks(sp, limit=50, time_range='medium_term'):
    top_tracks = sp.current_user_top_tracks(limit=limit, time_range=time_range)
    return top_tracks['items']


def get_recommendations(sp, seed_tracks=None, limit=100):
    recommendations = sp.recommendations(seed_tracks=seed_tracks, limit=limit)
    return recommendations['tracks']


def filter_tracks_by_tempo(sp, tracks, target_tempo, tempo_tolerance=2):
    tracks_ids = [track['id'] for track in tracks]
    audio_features = sp.audio_features(tracks=tracks_ids)

    filtered_tracks = []
    for track, features in zip(tracks, audio_features):
        if features and abs(features['tempo'] - target_tempo) <= tempo_tolerance:
            filtered_tracks.append(track)

    return filtered_tracks


def create_playlist(sp, user_id, name, description):
    playlist = sp.user_playlist_create(user_id, name, description=description)
    return playlist['id']


def add_tracks_to_playlist(sp, playlist_id, tracks):
    if not tracks:
        print("No tracks to add to the playlist.")
        return
    track_ids = [track['id'] for track in tracks]
    sp.playlist_add_items(playlist_id, track_ids)


# Main function
def main():
    display_banner()
    target_tempo = int(input("Enter desired tempo (bpm): "))  # Desired tempo
    tempo_tolerance = int(input("Specify +- bpm tolerance (low tolerance may lead to a short playlist): "))  # Tolerance
    playlist_length = int(input("Minimum playlist length (no. of tracks): "))

    user_id = sp.current_user()['id']

    # Get top tracks
    top_tracks = get_top_tracks(sp)
    seed_tracks = [track['id'] for track in top_tracks[:5]]  # Use top tracks as seeds

    # Get recommended tracks and filter by tempo
    filtered_tracks = []
    while len(filtered_tracks) < playlist_length:
        recommended_tracks = get_recommendations(sp, seed_tracks=seed_tracks, limit=100)
        new_filtered_tracks = filter_tracks_by_tempo(sp, recommended_tracks, target_tempo, tempo_tolerance)

        # Add only new tracks to avoid duplicates
        new_filtered_tracks_ids = {track['id'] for track in new_filtered_tracks}
        existing_filtered_tracks_ids = {track['id'] for track in filtered_tracks}
        unique_new_tracks = [track for track in new_filtered_tracks if track['id'] not in existing_filtered_tracks_ids]

        filtered_tracks.extend(unique_new_tracks)

        # Check if we have enough unique recommendations to proceed
        if len(recommended_tracks) < 100:
            break

    # Ensure there are enough tracks to create a playlist
    if len(filtered_tracks) < playlist_length:
        print("Not enough tracks. Try increasing tempo tolerance and/or reducing playlist length.")
        return

    # Create a new playlist
    playlist_name = input("Playlist name: ")
    playlist_description = input("Playlist description: ")
    playlist_id = create_playlist(sp, user_id, playlist_name, playlist_description)

    # Add tracks to the new playlist
    add_tracks_to_playlist(sp, playlist_id, filtered_tracks)
    print(f"Playlist '{playlist_name}' created with {len(filtered_tracks)} tracks.")


if __name__ == "__main__":
    main()
