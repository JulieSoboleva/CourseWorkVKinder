import re
from bot_api.finder import VK_Finder
from logic.service import Service
from config import app_token


class VK_Bot:

    def __init__(self, client_id, vk_api):
        print("\nСоздан объект бота")
        info = vk_api.method('users.get', {'user_ids': client_id,
                                           'fields': 'sex,city'})
        self._USER_ID = client_id
        self._USERNAME = info[0]['first_name']
        self._CITY = info[0]['city']['title']
        self._DB = Service()
        self._DB.add_client(vk_id=client_id, first_name=self._USERNAME,
                            last_name=info[0]['last_name'], city=self._CITY,
                            gender='Ж' if info[0]['sex'] == 1 else 'М')
        self._COMMANDS = ['ПРИВЕТ', 'М', 'Ж', '+', 'ПОКА']
        self._VK_FINDER = VK_Finder(app_token=app_token, user_id=client_id)
        self.search_params = {}

    def new_message(self, message):
        # Привет
        if message.upper() == self._COMMANDS[0]:
            return f'Привет, {self._USERNAME}! ' \
                   f'Я могу помочь тебе найти человека.' \
                   f'\nКого ты ищешь? (Введи М или Ж)'
        # Пол
        elif (message.upper() == self._COMMANDS[1] or
              message.upper() == self._COMMANDS[2]):
            self.search_params['gender'] = message.upper()
            return self.get_next_question()
        # Свой город
        elif message.upper() == self._COMMANDS[3]:
            self.search_params['city'] = self._CITY
            return self.get_next_question()
        # Пока
        elif message.upper() == self._COMMANDS[4]:
            return f"Пока-пока, {self._USERNAME}!"
        # Другой населённый пункт
        elif message.startswith('@'):
            self.search_params['city'] = message[1:].capitalize()
            return self.get_next_question()
        # Возрастной интервал
        elif message is not None:
            ages = re.match(r'(\d{2})\s*-\s*(\d{2})', message)
            print('groups count =', len(ages.groups()))
            if len(ages.groups()) == 2:
                self.search_params['age_from'] = ages.group(1)
                self.search_params['age_to'] = ages.group(2)
                return self.get_next_question()
            return "Не понимаю о чем вы..."

    def get_next_question(self) -> str:
        if self.search_params.get('gender') is None:
            return 'Кого ты ищешь? (Введи М или Ж)'
        if self.search_params.get('city') is None:
            return f'В каком городе будем искать? ' \
                   f'(Введи + если в твоём городе ({self._CITY}) или ' \
                   f'название населённого пункта в формате: "@Пермь")'
        if self.search_params.get('age_from') is None:
            return f'Укажи возрастной интервал в формате: "20 - 40".' \
                   f'(Минимальный возраст - 16 лет, максимальный - 99)'
        if self.search_params.get('age_to') is None:
            return f'Укажи возрастной интервал в формате: "20 - 40".' \
                   f'(Минимальный возраст - 16 лет, максимальный - 99)'
        return 'Все параметры заданы. Пошёл искать...'

    def get_candidates_list(self):
        query_id = self._DB.has_query(self._USER_ID,
                                      self.search_params['gender'],
                                      self.search_params['city'],
                                      self.search_params['age_from'],
                                      self.search_params['age_to'])
        if query_id != 0:
            return self._DB.get_persons()

        self._DB.add_query(self._USER_ID, self.search_params['gender'],
                           self.search_params['city'],
                           self.search_params['age_from'],
                           self.search_params['age_to'])

        candidates = self._VK_FINDER.get_pretendents(
            self.search_params['age_from'], self.search_params['age_to'],
            self.search_params['gender'], self.search_params['city'])

        for person in candidates:
            # self._DB.add_person()
            print(person)

        print('Список сформирован')
