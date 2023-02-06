import requests
import time


class VkUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version):
        self.params = {
            'access_token': token,
            'v': version
        }

    def get_group_id_by_screen_name(self, screen_name):
        get_group_url = self.url + 'groups.getById'
        get_group_params = {'group_id': screen_name}
        result = requests.get(get_group_url, params={**self.params, **get_group_params}).json()
        if 'error' in result:
            group_id = 0
        else:
            group_id = f"-{result['response'][0]['id']}"
        return group_id

    def get_user_id_by_screen_name(self, screen_name):
        get_user_url = self.url + 'users.get'
        get_user_params = {'user_ids': screen_name}
        result = requests.get(get_user_url, params={**self.params, **get_user_params}).json()
        if result['response']:
            user_id = result['response'][0]['id']
        else:
            user_id = self.get_group_id_by_screen_name(screen_name)
        return user_id

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