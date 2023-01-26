import requests
import time


class VkUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version):
        self.params = {
            'access_token': token,
            'v': version
        }

    def photos_get(self, owner_id, album_id='profile', photos_count=1000):
        photos_get_url = self.url + 'photos.get'
        if photos_count < 1000:
            count = photos_count
        else:
            count = 1000
        photos_get_params = {
            'owner_id': owner_id,
            'album_id': album_id,
            'count': count,
            'extended': 1,
            'photo_sizes': 1
        }
        result = requests.get(photos_get_url, params={**self.params, **photos_get_params}).json()
        if photos_count >= 1000 and result['response']['count'] > 1000:
            offset = 0
            while offset < result['response']['count']:
                offset += 1000
                time.sleep(0.34)
                next_res = requests.get(photos_get_url, params={
                    **self.params,
                    **photos_get_params,
                    'offset': offset
                }).json()
                result['response']['items'].extend(next_res['response']['items'])
        return result