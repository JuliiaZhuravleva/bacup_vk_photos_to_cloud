import json
from vk import VkUser
from ya_disk import YandexDisk
from urllib.parse import urlparse
from datetime import datetime
import os.path
import PySimpleGUI as sg


def __select_max_size_photo__(sizes):
    size_scale = ['r', 'q', 'p', 'o', 's', 'm', 'x', 'y', 'z', 'w']
    max_size = 0
    for size in sizes:
        if size_scale.index(size['type']) > max_size:
            max_size = size_scale.index(size['type'])
            max_size_photo = size
    return max_size_photo


def filter_photo_info(photo_info):
    new_photo_info = {
        'likes': photo_info['likes']['count'],
        'date': datetime.fromtimestamp(photo_info['date']).strftime('%d-%m-%y_%H-%M-%S'),
        **__select_max_size_photo__(photo_info['sizes'])
    }
    return new_photo_info


def file_ext(url):
    path = urlparse(url).path
    ext = os.path.splitext(path)[1]
    return ext


if __name__ == "__main__":
    # sg.theme('DarkGrey5')
    vk_albums = {
        'Фото профиля': 'profile',
        'Фото со стены': 'wall',
        'Сохраненные фото': 'saved',
        'Идентификатор альбома': None}
    col1 = [[sg.Text('Введите id пользователя Вконтаксте'),
             sg.InputText(key='-vk_id-', right_click_menu=[[''], ['Paste vk id']])],
            [sg.Text('Введите токен Яндекс диска'),
             sg.InputText(key='-ya_token-', right_click_menu=[[''], ['Paste ya token']])],
            [sg.Text('Выберите альбом'),
             sg.Combo(key='-album-',
                      values=list(vk_albums.keys()),
                      default_value='Фото профиля',
                      enable_events=True)],
            [sg.Text('Введите идентификатор альбома', visible=False, key='-album_id_text-'),
             sg.InputText(key='-album_id-', visible=False)],
            [sg.Text('Введите количество фото'),
             sg.InputText(key='-photo_count-', default_text='5', right_click_menu=[[''], ['Paste count']])],
            [sg.Text(size=(40,1), key='-OUTPUT-')],
            [sg.Button('Ввод'), sg.Button('Отмена')]]
    col2 = [[sg.Image('logo.png', size=(278, 278))]]
    layout = [[sg.Text('Загрузка фото из Вконтакте на Яндекс диск')],
        [sg.Column(col1, element_justification='b'), sg.Column(col2)]]
    window = sg.Window('Загрузка фото из Вконтакте на Яндекс диск', layout)
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Отмена' or event == 'Спасибо!':
            break
        elif event == 'Paste vk id':
            window['-vk_id-'].update(sg.clipboard_get())
        elif event == 'Paste ya token':
            window['-ya_token-'].update(sg.clipboard_get())
        elif event == '-album-' and values['-album-'] == 'Идентификатор альбома':
            window['-album_id_text-'].update(visible=True)
            window['-album_id-'].update(visible=True)
        elif event == '-album-' and values['-album-'] != 'Идентификатор альбома':
            window['-album_id_text-'].update(visible=False)
            window['-album_id-'].update(visible=False)
        if event == 'Ввод':
            if not values['-vk_id-']:
                window['-OUTPUT-'].update('Нужно указать id пользователя вконтакте!', text_color='red')
            elif not values['-ya_token-']:
                window['-OUTPUT-'].update('Нужно указать токен Яндекс диска!', text_color='red')
            elif not values['-photo_count-'] or not values['-photo_count-'].isnumeric():
                window['-OUTPUT-'].update('Укажите количество фото', text_color='red')
            elif not values['-album-'] or values['-album-'] not in vk_albums.keys():
                window['-OUTPUT-'].update('Выберите альбом', text_color='red')
            elif values['-album-'] == 'Идентификатор альбома' and not values['-album_id-'].isnumeric():
                window['-OUTPUT-'].update('Введите идентификатор альбома', text_color='red')
            else:
                vk_user_id = values['-vk_id-']
                yadisk_token = values['-ya_token-']
                photos_count = int(values['-photo_count-'])
                window['-OUTPUT-'].update('Подготовка файлов...', text_color='yellow')

                with open('token.txt', 'r') as file_object:
                    access_token = file_object.read().strip()

                if values['-album-'] == 'Идентификатор альбома':
                    album_id = values['-album_id-']
                else:
                    album_id = vk_albums[values['-album-']]

                vk_client = VkUser(access_token, '5.131')
                my_photos_info_full = vk_client.photos_get(vk_user_id, album_id, photos_count)
                if 'error' in my_photos_info_full:
                    if my_photos_info_full['error']['error_code'] == 7:
                        window['-OUTPUT-'].update('Фотоальбом должен быть открытым!', text_color='red')
                    else:
                        window['-OUTPUT-'].update('Некорректный id пользователя вконтакте!', text_color='red')
                    continue
                total_photos_count = len(my_photos_info_full['response']['items'])
                my_photos_info = []
                likes = []
                for info in my_photos_info_full['response']['items']:
                    new_info = filter_photo_info(info)
                    my_photos_info.append(new_info)
                    likes.append(new_info['likes'])

                yadisk_client = YandexDisk(yadisk_token)
                if yadisk_client.create_folder('vk_photos_'+album_id) == 'error':
                    window['-OUTPUT-'].update('Некорректный токен Яндекс диска!', text_color='red')
                    continue

                window.close()

                json_file = []
                for i, photo in enumerate(my_photos_info):
                    if likes.count(photo['likes']) == 1:
                        file_name = str(photo['likes']) + file_ext(photo['url'])
                    else:
                        file_name = str(photo['likes']) + '_' + str(photo['date']) + file_ext(photo['url'])
                    yadisk_client.upload_file_to_disk('vk_photos_' + album_id + '/' + file_name, photo['url'], True)
                    json_file.append({'file_name': file_name, 'size': photo['type']})
                    sg.one_line_progress_meter('Загрузка фотографий на Яндекс диск',
                                               i + 1,
                                               total_photos_count,
                                               'Подождите, идет процесс загрузки')

                with open('photos_info.json', 'w') as writer:
                    json.dump(json_file, writer)
                yadisk_client.upload_file_to_disk('vk_photos_' + album_id + '/photos_info.json', 'photos_info.json')
                os.remove('photos_info.json')
                window = sg.Window('Готово', [[sg.Text('Процесс передачи фотографий завершен! :)')],
                                              [sg.Button('Спасибо!')]])



