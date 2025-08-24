from .routes import add_route

# Albums endpoints
add_route(method="GET", path="/albums/{id}", params={"id": "4aawyAB9vmqN3uQ7FjRGTy"})
add_route(method="GET", path="/albums")
add_route(method="GET", path="/albums/{id}/tracks", params={"id": "4aawyAB9vmqN3uQ7FjRGTy"})

# Artists endpoints
add_route(method="GET", path="/artists/{id}", params={"id": "0TnOYISbd1XYRBk9myaseg"})
add_route(method="GET", path="/artists")
add_route(method="GET", path="/artists/{id}/albums", params={"id": "0TnOYISbd1XYRBk9myaseg"})
add_route(method="GET", path="/artists/{id}/top-tracks", params={"id": "0TnOYISbd1XYRBk9myaseg"})
add_route(method="GET", path="/artists/{id}/related-artists", params={"id": "0TnOYISbd1XYRBk9myaseg"})

# Tracks endpoints
add_route(method="GET", path="/tracks/{id}", params={"id": "11dFghVXANMlKmJXsNCbNl"})
add_route(method="GET", path="/tracks")
add_route(method="GET", path="/audio-features/{id}", params={"id": "11dFghVXANMlKmJXsNCbNl"})
add_route(method="GET", path="/audio-features")
add_route(method="GET", path="/audio-analysis/{id}", params={"id": "11dFghVXANMlKmJXsNCbNl"})

# Playlists endpoints
add_route(method="GET", path="/playlists/{playlist_id}", params={"playlist_id": "3cEYpjA9oz9GiPac4AsH4n"})
add_route(method="POST", path="/playlists")
add_route(method="PUT", path="/playlists/{playlist_id}", params={"playlist_id": "3cEYpjA9oz9GiPac4AsH4n"})
add_route(method="GET", path="/playlists/{playlist_id}/tracks", params={"playlist_id": "3cEYpjA9oz9GiPac4AsH4n"})
add_route(method="POST", path="/playlists/{playlist_id}/tracks", params={"playlist_id": "3cEYpjA9oz9GiPac4AsH4n"})
add_route(method="PUT", path="/playlists/{playlist_id}/tracks", params={"playlist_id": "3cEYpjA9oz9GiPac4AsH4n"})
add_route(method="DELETE", path="/playlists/{playlist_id}/tracks", params={"playlist_id": "3cEYpjA9oz9GiPac4AsH4n"})
add_route(method="GET", path="/playlists/{playlist_id}/images", params={"playlist_id": "3cEYpjA9oz9GiPac4AsH4n"})
add_route(method="PUT", path="/playlists/{playlist_id}/images", params={"playlist_id": "3cEYpjA9oz9GiPac4AsH4n"})

# User endpoints
add_route(method="GET", path="/me")
add_route(method="GET", path="/users/{user_id}", params={"user_id": "smedjan"})
add_route(method="GET", path="/me/playlists")
add_route(method="GET", path="/users/{user_id}/playlists", params={"user_id": "smedjan"})
add_route(method="GET", path="/me/albums")
add_route(method="PUT", path="/me/albums")
add_route(method="DELETE", path="/me/albums")
add_route(method="GET", path="/me/tracks")
add_route(method="PUT", path="/me/tracks")
add_route(method="DELETE", path="/me/tracks")
add_route(method="GET", path="/me/following")
add_route(method="PUT", path="/me/following")
add_route(method="DELETE", path="/me/following")
add_route(method="GET", path="/me/top/artists")
add_route(method="GET", path="/me/top/tracks")

# Player endpoints
add_route(method="GET", path="/me/player")
add_route(method="GET", path="/me/player/devices")
add_route(method="GET", path="/me/player/currently-playing")
add_route(method="PUT", path="/me/player/play")
add_route(method="PUT", path="/me/player/pause")
add_route(method="POST", path="/me/player/next")
add_route(method="POST", path="/me/player/previous")
add_route(method="PUT", path="/me/player/seek")
add_route(method="PUT", path="/me/player/repeat")
add_route(method="PUT", path="/me/player/volume")
add_route(method="PUT", path="/me/player/shuffle")
add_route(method="PUT", path="/me/player")
add_route(method="POST", path="/me/player/queue")
add_route(method="GET", path="/me/player/recently-played")

# Search endpoint
add_route(method="GET", path="/search")

# Browse endpoints
add_route(method="GET", path="/browse/new-releases")
add_route(method="GET", path="/browse/featured-playlists")
add_route(method="GET", path="/browse/categories")
add_route(method="GET", path="/browse/categories/{category_id}", params={"category_id": "toplists"})
add_route(method="GET", path="/browse/categories/{category_id}/playlists", params={"category_id": "toplists"})

# Shows and episodes endpoints
add_route(method="GET", path="/shows/{id}", params={"id": "38bS44xjbVVZ3No3ByF1dJ"})
add_route(method="GET", path="/shows")
add_route(method="GET", path="/shows/{id}/episodes", params={"id": "38bS44xjbVVZ3No3ByF1dJ"})
add_route(method="GET", path="/episodes/{id}", params={"id": "512ojhOuo1ktJprKbVcKyQ"})
add_route(method="GET", path="/episodes")
add_route(method="GET", path="/me/shows")
add_route(method="PUT", path="/me/shows")
add_route(method="DELETE", path="/me/shows")
add_route(method="GET", path="/me/episodes")
add_route(method="PUT", path="/me/episodes")
add_route(method="DELETE", path="/me/episodes")

# Markets and genres
add_route(method="GET", path="/markets")
add_route(method="GET", path="/recommendations/available-genre-seeds")
add_route(method="GET", path="/recommendations")

# Basic endpoints
add_route(method="GET", path="/")
add_route(method="GET", path="/health")


def init_cases() -> None:
    pass


__all__ = [
    "init_cases",
]
