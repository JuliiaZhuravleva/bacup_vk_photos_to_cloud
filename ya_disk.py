import requests


class YandexDisk:
    url = 'https://cloud-api.yandex.net/v1/disk/resources/'

    def __init__(self, token):
        self.token = token

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def _get_upload_link(self, disk_file_path):
        upload_url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        headers = self.get_headers()
        params = {"path": disk_file_path, "overwrite": "true"}
        response = requests.get(upload_url, headers=headers, params=params)
        return response.json()

    def upload_file_to_disk(self, disk_file_path, file, url=False):
        href = self._get_upload_link(disk_file_path=disk_file_path).get("href", "")
        if url:
            data = requests.get(file).content
        else:
            data = open(file, 'rb')
        response = requests.put(href, data=data)
        response.raise_for_status()

    def create_folder(self, path):
        params = {'path': path}
        response = requests.put(self.url, headers=self.get_headers(), params=params)
        if response.status_code != 409 and response.status_code !=201:
            return 'error'

