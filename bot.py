import re
from bot_api.finder import VK_Finder
from logic.service import Service
from config import app_token
from vk_api.keyboard import VkKeyboard, VkKeyboardColor


class VK_Bot:

    def __init__(self, client_id, vk_api):
        print("\nСоздан объект бота")
        info = vk_api.method('users.get', {'user_ids': client_id,
                                           'fields': 'sex,city'})
        self.user_id = client_id
        self.user_name = info[0]['first_name']
        self.user_city = info[0]['city']['title']
        self.db = Service()
        self.query_id = 0
        self.search_params = {}
        if self.db.find_client(client_id):
            self.query_id = self.db.get_last_query(client_id)
        else:
            self.db.add_client(vk_id=client_id, first_name=self.user_name,
                               last_name=info[0]['last_name'],
                               city=self.user_city,
                               gender='Ж' if info[0]['sex'] == 1 else 'М')
        self.COMMANDS = ['М', 'Ж', '+', 'ПОКА', 'В ИЗБРАННОЕ', 'СЛЕДУЮЩИЙ',
                         'ТОЧНО НЕТ', 'СТОП', 'ПРЕДЫДУЩИЙ', 'НОВЫЙ ПОИСК',
                         'НАЧАТЬ']
        self.vk_finder = VK_Finder(app_token=app_token, user_id=client_id)
        self.start = True
        self.stop = False
        self.counter = 0
        self.candidates = None
        self.keyboard = None
        self.attachment = None

    def new_message(self, message) -> str:
        message = message.upper().strip()
        if self.start or message == self.COMMANDS[10]:
            self.start = False
            self.attachment = None
            if self.query_id == 0:
                self.keyboard = None
                text = f'Привет, {self.user_name}!\n' \
                       f'Я могу помочь тебе найти человека.\n' \
                       f'Для этого нужно будет ответить на несколько вопросов.\n' \
                       f'Если захочешь прервать текущий поиск ' \
                       f'или просмотр кандидатур, набери "пока".\n' \
                       f'Для прекращения работы программы, введи "стоп".\n' \
                       f'\nИтак, кого ты ищешь? (Введи М или Ж)'
            else:
                self.keyboard = self.create_query_buttons()
                text = f'Привет, {self.user_name}!\nДавно не виделись!\n' \
                       f'Показать результаты предыдущего запроса ' \
                       f'или начнём новый поиск?'
            return text
        elif message == self.COMMANDS[9]:
            self.keyboard = None
            return 'Кого на этот раз будем искать? (Введи М или Ж)'
        # Пол
        elif message == self.COMMANDS[0] or message == self.COMMANDS[1]:
            self.search_params['gender'] = message
            self.attachment = None
            self.keyboard = None
            return self.get_next_question()
        # Свой город
        elif message == self.COMMANDS[2]:
            self.search_params['city'] = self.user_city
            self.attachment = None
            self.keyboard = None
            return self.get_next_question()
        # Пока
        elif message == self.COMMANDS[3]:
            self.keyboard = None
            text = f"Пока-пока, {self.user_name}!"
            if self.counter <= len(self.candidates):
                text += f'\n\nЭто ещё не все кандидаты, ' \
                        'но ты сможешь вернуться к просмотру позже,' \
                        ' набрав "начать".'
            self.attachment = None
            self.candidates = None
            self.counter = 0
            return text
        # Другой населённый пункт
        elif message.startswith('@'):
            self.search_params['city'] = message[1:].capitalize()
            self.attachment = None
            self.keyboard = None
            return self.get_next_question()
        # Демонстрация фоток
        elif message in (self.COMMANDS[4], self.COMMANDS[5],
                         self.COMMANDS[6], self.COMMANDS[8]):
            params = ''
            if message == self.COMMANDS[4]:
                self.db.add_to_favourites(
                    self.user_id, self.candidates[self.counter-1]['id'])
            elif message == self.COMMANDS[6]:
                self.db.delete_from_candidates(
                    self.query_id, self.candidates[self.counter-1]['id'])
            elif message == self.COMMANDS[8]:
                self.candidates = self.db.get_persons(self.query_id,
                                                      self.user_id)
                params = self.db.get_query_params(self.query_id)
                params += f'\nОсталось просмотреть: {len(self.candidates)}\n\n'
            self.keyboard = self.create_buttons()
            self.counter += 1
            if self.counter > len(self.candidates):
                self.keyboard = None
                self.attachment = None
                favourites_list = self.db.get_favourites(self.user_id,
                                                         self.query_id)
                if len(favourites_list) > 0:
                    text = 'Список избранных:\n' + '\n'.join(favourites_list)
                else:
                    text = 'Список избранных пуст.'
                return 'Конец показа\n\n' + text
            person = self.candidates[self.counter - 1]
            self.attachment = person['photos']
            return params + person['name'] + ' ' + person['surname']
        # Выход из программы
        elif message == self.COMMANDS[7]:
            self.stop = True
            self.keyboard = None
            self.attachment = None
            return 'Всё-всё. Выключаюсь.'
        # Возрастной интервал
        elif message is not None:
            self.keyboard = None
            self.attachment = None
            ages = re.match(r'(\d{2})\s*-\s*(\d{2,3})', message)
            if ages is not None and len(ages.groups()) == 2:
                self.search_params['age_from'] = ages.group(1)
                self.search_params['age_to'] = ages.group(2)
                return self.get_next_question()
            return "Не понимаю о чем ты..."

    def create_buttons(self):
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button(self.COMMANDS[4], VkKeyboardColor.POSITIVE)
        keyboard.add_button(self.COMMANDS[5], VkKeyboardColor.PRIMARY)
        keyboard.add_button(self.COMMANDS[6], VkKeyboardColor.NEGATIVE)
        return keyboard

    def create_query_buttons(self):
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button(self.COMMANDS[8], VkKeyboardColor.SECONDARY)
        keyboard.add_button(self.COMMANDS[9], VkKeyboardColor.SECONDARY)
        return keyboard

    def get_next_question(self) -> str:
        if self.search_params.get('gender') is None:
            return 'Кого будем искать? (Введи М или Ж)'
        if self.search_params.get('city') is None:
            return f'В каком городе будем искать?\n' \
                   f'(Введи "+" если в твоём городе ({self.user_city}) или ' \
                   f'название населённого пункта в формате: "@Пермь")'
        if self.search_params.get('age_from') is None:
            return f'Укажи возрастной интервал в формате: "20 - 40".\n' \
                   f'(Минимальный возраст - 16 лет, максимальный - 99)'
        if self.search_params.get('age_to') is None:
            return f'Укажи возрастной интервал в формате: "20 - 40".\n' \
                   f'(Минимальный возраст - 16 лет, максимальный - 99)'
        self.check_age_params()
        return f'Все параметры заданы:\n' \
               f'{"мужчина" if self.search_params["gender"] == "М" else "женщина"},' \
               f' возраст: {self.search_params["age_from"]} - ' \
               f'{self.search_params["age_to"]}, {self.search_params["city"]}' \
               f'\n\nНачинаю поиск...'

    def get_candidates_list(self):
        self.query_id = self.db.has_query(self.user_id,
                                          self.search_params['gender'],
                                          self.search_params['city'],
                                          self.search_params['age_from'],
                                          self.search_params['age_to'])
        if self.query_id != 0:
            return self.db.get_persons(self.query_id, self.user_id)

        self.query_id = self.db.add_query(self.user_id,
                                          self.search_params['gender'],
                                          self.search_params['city'],
                                          self.search_params['age_from'],
                                          self.search_params['age_to'])
        candidates = self.vk_finder.get_pretendents(
            self.search_params['age_from'], self.search_params['age_to'],
            self.search_params['gender'], self.search_params['city'])
        self.db.add_persons(self.query_id, candidates)
        print(f'Список сформирован и записан в БД. Кандидатов: {len(candidates)}')
        return self.db.get_persons(self.query_id, self.user_id)

    def find_candidates(self) -> str:
        self.counter = 0
        self.candidates = self.get_candidates_list()
        self.search_params = {}
        if len(self.candidates) < 1:
            return f'Не нашёл подходящих под запрос людей.\n\n' \
                   f'Попробуй сформировать новый запрос.'
        self.keyboard = self.create_buttons()
        self.counter += 1
        person = self.candidates[self.counter - 1]
        self.attachment = person['photos']
        return f'Нашёл подходящих людей: {len(self.candidates)}\n\n' \
               + person['name'] + ' ' + person['surname']

    def check_age_params(self):
        if int(self.search_params['age_from']) < 16:
            self.search_params['age_from'] = 16
        if int(self.search_params['age_to']) > 99:
            self.search_params['age_to'] = 99
        elif int(self.search_params['age_to']) < 16:
            self.search_params['age_to'] = 16
        if (int(self.search_params['age_from']) >
                int(self.search_params['age_to'])):
            self.search_params['age_from'], self.search_params['age_to'] = \
                self.search_params['age_to'], self.search_params['age_from']
