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

    user_id = sp.current_user()['id']

    # Get top tracks
    top_tracks = get_top_tracks(sp)
    seed_tracks = [track['id'] for track in top_tracks[:5]]  # Use top tracks as seeds

    # Get recommended tracks
    recommended_tracks = get_recommendations(sp, seed_tracks=seed_tracks, limit=100)

    # Filter tracks by tempo
    filtered_tracks = filter_tracks_by_tempo(sp, recommended_tracks, target_tempo, tempo_tolerance)

    # Ensure there are tracks to add
    if not filtered_tracks:
        print("No tracks found with the specified tempo.")
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
