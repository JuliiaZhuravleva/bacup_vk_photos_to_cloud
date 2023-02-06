import json
from urllib.parse import urlparse
from datetime import datetime
import os.path

from vk import VkUser
from ya_disk import YandexDisk

import PySimpleGUI as sg
import configparser


vk_albums = {
    'Фото профиля': 'profile',
    'Фото со стены': 'wall',
    'Сохраненные фото': 'saved',
    'Идентификатор альбома': None
}


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


def read_config():
    config = configparser.ConfigParser()
    config.read("settings.ini")

    vk_token = config['tokens']['vk_token']
    yadisk_token = config['tokens']['yadisk_token']

    return {'vk_token': vk_token, 'yadisk_token': yadisk_token}


def call_input_window():
    sg.theme('TanBlue')
    col1 = [[sg.Text('Введите id пользователя vk'),
             sg.InputText(size=(20, 25),
                          key='-vk_id-',
                          right_click_menu=[[''], ['Paste vk id']])],
            [sg.Text('Выберите альбом'),
             sg.Combo(size=(25, 25),
                      key='-album-',
                      values=list(vk_albums.keys()),
                      default_value='Фото профиля',
                      enable_events=True)],
            [sg.Text('Введите идентификатор альбома', visible=False, key='-album_id_text-'),
             sg.InputText(size=(20, 25), key='-album_id-', visible=False)],
            [sg.Text('Введите количество фото'),
             sg.InputText(size=(10, 25),
                          key='-photo_count-',
                          default_text='5',
                          right_click_menu=[[''], ['Paste count']])],
            [sg.Text(size=(40, 1), key='-OUTPUT-')],
            [sg.Button('Ввод', bind_return_key=True), sg.Button('Отмена')]]
    col2 = [[sg.Image('logo.png', size=(278, 278))]]
    layout = [[sg.Text('Загрузка фото из Вконтакте на Яндекс диск')],
              [sg.Column(col1, element_justification='r'), sg.Column(col2)]]
    window = sg.Window('Загрузка фото из Вконтакте на Яндекс диск', layout, return_keyboard_events=True)
    return window


def read_from_window(window, vk_client):
    event, values = window.read()

    output_values = {}
    action = ''

    if event == sg.WIN_CLOSED or event == 'Отмена' or event == 'Спасибо!':
        action = 'break'
    elif event == 'Paste vk id':
        window['-vk_id-'].update(sg.clipboard_get())
    elif event == '-album-' and values['-album-'] == 'Идентификатор альбома':
        window['-album_id_text-'].update(visible=True)
        window['-album_id-'].update(visible=True)
    elif event == '-album-' and values['-album-'] != 'Идентификатор альбома':
        window['-album_id_text-'].update(visible=False)
        window['-album_id-'].update(visible=False)
    elif event == 'Ввод':
        if not values['-vk_id-']:
            show_errors(window, 'Нужно указать id пользователя вконтакте!')
        elif not values['-photo_count-'] or not values['-photo_count-'].isnumeric():
            show_errors(window, 'Укажите количество фото')
        elif not values['-album-'] or values['-album-'] not in vk_albums.keys():
            show_errors(window, 'Выберите альбом')
        elif values['-album-'] == 'Идентификатор альбома' and not values['-album_id-'].isnumeric():
            show_errors(window, 'Введите идентификатор альбома')
        else:
            action = 'load_photos'
            if not values['-vk_id-'].lstrip('-').isnumeric():
                output_values['vk_id'] = vk_client.get_user_id_by_screen_name(values['-vk_id-'])
            else:
                output_values['vk_id'] = values['-vk_id-']
            output_values['photos_count'] = int(values['-photo_count-'])
            if values['-album-'] == 'Идентификатор альбома':
                output_values['album'] = values['-album_id-']
            else:
                output_values['album'] = vk_albums[values['-album-']]

    return {'action': action, 'values': output_values}


def show_errors(window, error):
    window['-OUTPUT-'].update(error, text_color='red')


def get_vk_photos(window, vk_client, vk_user_id, album_id, photos_count):
    action = ''
    photos_info = []
    likes = []

    photos_info_full = vk_client.photos_get(vk_user_id, album_id, photos_count)
    if 'error' in photos_info_full:
        if photos_info_full['error']['error_code'] in [7, 200]:
            show_errors(window, 'Фотоальбом должен быть открытым!')
        else:
            show_errors(window, 'Некорректный id пользователя вконтакте!')
        action = 'continue'
    else:
        for info in photos_info_full['response']['items']:
            new_info = filter_photo_info(info)
            photos_info.append(new_info)
            likes.append(new_info['likes'])
    return {'action': action, 'photos_info': photos_info, 'likes': likes}


def upload_photos_to_yadisk(photos_info, album_name, yadisk_client):
    json_file = []
    total_photos_count = len(photos_info)
    for i, photo in enumerate(photos_info['photos_info']):
        if photos_info['likes'].count(photo['likes']) == 1:
            file_name = str(photo['likes']) + file_ext(photo['url'])
        else:
            file_name = str(photo['likes']) + '_' + str(photo['date']) + file_ext(photo['url'])
        yadisk_client.upload_file_to_disk('vk_photos_' + album_name + '/' + file_name, photo['url'], True)
        json_file.append({'file_name': file_name, 'size': photo['type']})
        sg.one_line_progress_meter('Загрузка фотографий на Яндекс диск',
                                   i + 1,
                                   total_photos_count,
                                   'Подождите, идет процесс загрузки')

    with open('photos_info.json', 'w') as writer:
        json.dump(json_file, writer)
    yadisk_client.upload_file_to_disk('vk_photos_' + album_name + '/photos_info.json', 'photos_info.json')
    os.remove('photos_info.json')


if __name__ == "__main__":
    input_window = call_input_window()
    while True:
        my_vk_client = VkUser(read_config()['vk_token'], '5.131')
        read = read_from_window(input_window, my_vk_client)
        if read['action'] == 'break':
            break
        elif read['action'] == 'load_photos':
            given_vk_user_id = read['values']['vk_id']
            given_photos_count = read['values']['photos_count']
            given_album_id = read['values']['album']

            my_photos_info = get_vk_photos(
                window=input_window,
                vk_client=my_vk_client,
                vk_user_id=given_vk_user_id,
                album_id=given_album_id,
                photos_count=given_photos_count
            )

            if my_photos_info['action'] == 'continue':
                continue

            my_yadisk_client = YandexDisk(read_config()['yadisk_token'])
            if my_yadisk_client.create_folder('vk_photos_'+given_album_id) == 'error':
                show_errors(input_window, 'Некорректный токен Яндекс диска!')
                continue

            input_window.close()

            upload_photos_to_yadisk(
                photos_info=my_photos_info,
                album_name=given_album_id,
                yadisk_client=my_yadisk_client)

            input_window = sg.Window('Готово', [[sg.Text('Процесс передачи фотографий завершен! :)')],
                                                [sg.Button('Спасибо!')]])





