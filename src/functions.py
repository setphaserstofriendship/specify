import random


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


def get_top_tracks(sp, limit=50, time_range='long_term'):
    print("Fetching top tracks...")
    top_tracks = sp.current_user_top_tracks(limit=limit, time_range=time_range)
    return top_tracks['items']


def get_recommendations(sp, seed_tracks=None, limit=100):
    # print("Fetching recommendations...")
    recommendations = sp.recommendations(seed_tracks=seed_tracks, limit=limit)
    return recommendations['tracks']


def filter_tracks_by_tempo(sp, tracks, target_tempo, tempo_tolerance=2):
    # print("Filtering tracks by tempo...")
    tracks_ids = [track['id'] for track in tracks]
    audio_features = sp.audio_features(tracks=tracks_ids)

    filtered_tracks = []
    tempos = []  # To store the tempo of each filtered track
    for track, features in zip(tracks, audio_features):
        if features and abs(features['tempo'] - target_tempo) <= tempo_tolerance:
            filtered_tracks.append(track)
            tempos.append(features['tempo'])  # Store the tempo
    return filtered_tracks, tempos


def get_all_playlist_tracks(sp, user_id):
    print("Fetching all playlist tracks...")
    playlists = sp.user_playlists(user_id)
    all_tracks = set()
    for playlist in playlists['items']:
        tracks = sp.playlist_tracks(playlist['id'])
        for item in tracks['items']:
            all_tracks.add(item['track']['id'])
    return all_tracks


def create_playlist(sp, user_id, name, description):
    print(f"Creating playlist '{name}'...")
    playlist = sp.user_playlist_create(user_id, name, description=description)
    return playlist['id']


def add_tracks_to_playlist(sp, playlist_id, tracks):
    if not tracks:
        print("No tracks to add to the playlist.")
        return
    track_ids = [track['id'] for track in tracks]
    sp.playlist_add_items(playlist_id, track_ids)


def get_liked_songs(sp, limit=50):
    print("Fetching liked songs...")
    liked_songs = []
    results = sp.current_user_saved_tracks(limit=limit)
    liked_songs.extend(results['items'])

    # Continue fetching if there are more liked songs
    while results['next']:
        results = sp.next(results)
        liked_songs.extend(results['items'])
        if len(liked_songs) >= limit:
            break

    # Extract track information
    liked_tracks = [item['track'] for item in liked_songs]
    return liked_tracks


def get_random_seed_tracks(liked_tracks, seed_count=5):
    print(f"Selecting {seed_count} random tracks from liked songs...")

    if len(liked_tracks) < seed_count:
        print("Not enough liked tracks to seed. Returning all liked tracks.")
        seed_tracks = liked_tracks
    else:
        seed_tracks = random.sample(liked_tracks, seed_count)

    # Print the details of the selected tracks
    print("Selected tracks for seeding:")
    for track in seed_tracks:
        track_name = track['name']
        artist_names = ', '.join(artist['name'] for artist in track['artists'])
        print(f" - {track_name} by {artist_names}")

    return seed_tracks
