import json
import requests

class SpotifyClient:
    """SpotifyClient performs operations using the Spotify API."""

    def __init__(self, client_id, client_secret, base_url, auth_url):
        """
        :param client_id (str): Spotify app Client ID
        :param client_secret (str): Spotify app Client secret
        :param base_url (str): base URL of all Spotify Web API endpoints
        :param auth_url (str): Authentication URL
        """
        self._client_id = client_id
        self._client_secret = client_secret
        self._base_url = base_url
        self._auth_url = auth_url

        self._access_token = self.get_access_token()

    def get_access_token(self):
        """Authenticate and save access token

        :return access_token (str): Access token for supplied Client ID (Spotify for Developers App)
        """
        auth_response = requests.post(self._auth_url, {
            'grant_type': 'client_credentials',
            'client_id': self._client_id,
            'client_secret': self._client_secret,
        })
        auth_response_data = auth_response.json()
        access_token = auth_response_data['access_token']

        return access_token

    def _place_get_api_request(self, url, params):
        response = requests.get(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer {token}".format(token=self._access_token)
            },
            params=params
        )
        return response

    def _place_post_api_request(self, url, data):
        response = requests.post(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._authorization_token}"
            }
        )
        return response

    def get_artist_id_from_search(self, artist_name = ""):
        """Get the Spotify ID of an artist by his artist name. 
        IMPORTANT: Returns first result found. 
        This might not be the artist you had in mind in case there 
        are several artists with this name.

        :param artist_name (str): Name of artist
        :return artist_id (str): Spotify ID of first artist found by Spotify
        """
        url = self._base_url + 'search/'
        params={'q': artist_name, 
                'type': 'artist'}

        response = self._place_get_api_request(url, params)
        response_json = response.json()

        artist_id = response_json['artists']['items'][0]['id']

        return artist_id

    def get_top_tracks(self, artist_id, market="US"):
        url = self._base_url + 'artists/' + artist_id + "/top-tracks"
        params={'market': market}
        response = self._place_get_api_request(url, params)
        response_json = response.json()

        return response_json