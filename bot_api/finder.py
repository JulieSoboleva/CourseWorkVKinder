import traceback
import requests


class VK_Finder:
    def __init__(self, app_token, user_id):
        self.access_token = app_token
        self.vk_user_id = user_id
        self.version = '5.131'
        self.params = {'access_token': self.access_token, 'v': self.version}

    def get_photo_data(self, pretendent_id):
        """
        Запрашивает данные для загрузки фотографий методом photos.get
        """
        url = "https://api.vk.com/method/photos.get"
        params = {
            'owner_id': pretendent_id,
            'album_id': 'profile',
            'rev': 1,
            'extended': 1,
        }
        response = requests.get(url=url, params={**self.params, **params})
        result = response.json()
        photo_urls = []
        if 'response' in result:
            photos = result['response']['items']
            sorted_photos = sorted(photos,
                                   key=lambda x: x.get('likes', {}).get('count', 0),
                                   reverse=True)  # Сортировка по лайкам
            for photo in sorted_photos[:3]:
                photo_urls.append(photo['sizes'][-1]['url'])
        return photo_urls

    def get_pretendents(self, age_from, age_to, gender, city) -> list:
        """
        Получает id претендентов исходя из полученных ботом параметров
        :return:
        """
        params = {
            'count': '1000',
            'lang': 0,
            'sex': 1 if gender == 'Ж' else 2,
            'hometown': city,
            'age_from': age_from,
            'age_to': age_to,
            'has_photo': '1',
            'is_closed': False,
            'relation': 6,
        }
        url = 'https://api.vk.com/method/users.search'
        try:
            response = requests.get(url=url,
                                    params={**self.params, **params}).json()
            if response.get('error'):
                raise Exception(response['error']['error_msg'])

            if response['response']['count'] != 0:
                pretendents = []
                res = response['response']['items']
                for item in res:
                    profile_url = f"https://vk.com/id{item['id']}"
                    photos = self.get_photo_data(item['id'])
                    if photos:
                        pretendents.append({
                            'id': item['id'],
                            'name': item['first_name'],
                            'surname': item['last_name'],
                            'url': profile_url,
                            'photos': photos
                        })
                return pretendents
            else:
                raise Exception('Никого не нашёл')
        except Exception as err:
            print('Ошибка:\n', traceback.format_exc())
            return []
