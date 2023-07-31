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
        self.COMMANDS = ['М', 'Ж', '+', 'ПРАВИЛА', 'В ИЗБРАННОЕ', 'СЛЕДУЮЩИЙ',
                         'ТОЧНО НЕТ', 'СТОП', 'ПРЕДЫДУЩИЙ', 'НОВЫЙ ПОИСК',
                         'ЗАПРОС', 'ВЫХОД']
        self.vk_finder = VK_Finder(app_token=app_token, user_id=client_id)
        self.start = True
        self.stop = False
        self.counter = 0
        self.candidates = None
        self.keyboard = None
        self.attachment = None

    def new_message(self, message) -> str:
        message = message.upper().strip()
        if self.start:
            self.start = False
            self.reset()
            if self.query_id == 0:
                text = f'Привет, {self.user_name}!\n' \
                       f'Я могу помочь вам найти человека, не состоящего ' \
                       f'в отношениях.\nДля этого нужно будет ответить на ' \
                       f'несколько вопросов.\nДля прекращения работы ' \
                       f'программы введите "стоп".\nДля получения инструкции ' \
                       f'по командам введите "правила".' \
                       f'\nИтак, кого вы ищете? (Введи М или Ж)'
            else:
                self.keyboard = self.create_query_buttons()
                text = f'Привет, {self.user_name}!\nДавно не виделись!\n' \
                       f'Показать результаты одного из предыдущих запросов' \
                       f' или начнём новый поиск?'
            return text
        # Новый поиск постоянного клиента
        elif message == self.COMMANDS[9]:
            self.reset()
            return 'Кого на этот раз будем искать? (Введи М или Ж)'
        # Пол
        elif message == self.COMMANDS[0] or message == self.COMMANDS[1]:
            self.search_params['gender'] = message
            self.reset()
            return self.get_next_question()
        # Свой город
        elif message == self.COMMANDS[2]:
            self.search_params['city'] = self.user_city
            self.reset()
            return self.get_next_question()
        # Другой населённый пункт
        elif message.startswith('+'):
            self.search_params['city'] = message[1:].capitalize()
            self.reset()
            return self.get_next_question()
        # Стоп
        elif message == self.COMMANDS[7]:
            self.attachment = None
            self.keyboard = self.create_quite_buttons()
            text = f'{self.user_name}, вы уверены, что хотите остановить ' \
                   'работу бота?\nДля нового поиска просто начните вводить' \
                   ' его параметры по одному в произвольном порядке.\n' \
                   'Для получения списка запросов из БД напишите "запрос".'
            return text
        # Выход из программы
        elif message == self.COMMANDS[11]:
            self.stop = True
            self.reset()
            return 'Выключаюсь.'
        # Демонстрация фоток
        elif message in (self.COMMANDS[4], self.COMMANDS[5], self.COMMANDS[6])\
                or message.startswith('№'):
            params = ''
            if message == self.COMMANDS[4]:
                self.db.add_to_favourites(
                    self.user_id, self.candidates[self.counter-1]['id'])
            elif message == self.COMMANDS[6]:
                self.db.delete_from_candidates(
                    self.query_id, self.candidates[self.counter-1]['id'])
            elif message.startswith('№'):
                try:
                    self.query_id = int(message[1:])
                except ValueError:
                    return 'После № должно быть указано число.'
                self.candidates = self.db.get_persons(self.query_id,
                                                      self.user_id)
                params = self.db.get_query_params(self.query_id)
                params += f'\nОсталось просмотреть: {len(self.candidates)}\n\n'
            self.keyboard = self.create_buttons()
            self.counter += 1
            if self.counter > len(self.candidates):
                self.reset()
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
        # Правила игры
        elif message == self.COMMANDS[3]:
            self.reset()
            return '''
                Бот начинает работать при вводе любого первого сообщения от пользователя.
                * Для указания пола кандидата напишите "М" или "Ж".
                * Для указания возраста - введите диапазон в формате "20-25".
                * Для выбора локации поиска введите "+" или "+Город"
                * При просмотре найденных кандидатов можно добавлять их в список избранных
                или удалять из дальнейшего просмотра при помощи кнопок "В ИЗБРАННОЕ" и "ТОЧНО НЕТ".
                 * Для прекращения текущего сеанса работы введите "стоп".
                 * Для запуска нового поиска начните вводить параметры запроса по одному в произвольном порядке.
                 * Чтобы вернуться к любому из своих запросов, введите его номер после символа "№".
                 * Чтобы вывести список запросов напишите слово "запрос".
                 \n\n"Продолжаем разговор!" - как говорит мой друг Карлсон.'''
        # Выбор запроса
        elif message in (self.COMMANDS[8], self.COMMANDS[10]):
            self.reset()
            text = self.db.get_queries(self.user_id)
            if text != '':
                return text + '\n\nВыберите запрос, к которому хотите вернуться,' \
                              ' и введите его номер в формате "№1"'
            return 'В БД нет запросов данного клиента.'
        # Возрастной интервал
        elif message is not None:
            self.reset()
            ages = re.match(r'(\d{2})\s*-\s*(\d{2,3})', message)
            if ages is not None and len(ages.groups()) == 2:
                self.search_params['age_from'] = ages.group(1)
                self.search_params['age_to'] = ages.group(2)
                return self.get_next_question()
            return 'Не понимаю о чем вы... Наберите "правила" для получения' \
                   ' справки по работе с ботом.'

    def reset(self):
        self.keyboard = None
        self.attachment = None

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

    def create_quite_buttons(self):
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button(self.COMMANDS[11], VkKeyboardColor.SECONDARY)
        return keyboard

    def get_next_question(self) -> str:
        if self.search_params.get('gender') is None:
            return 'Кого будем искать? (Введи М или Ж)'
        if self.search_params.get('city') is None:
            return f'В каком городе будем искать?\n' \
                   f'(Введите "+", если в вашем городе ({self.user_city}) или ' \
                   f'название населённого пункта в формате: "+Волгоград")'
        if self.search_params.get('age_from') is None:
            return f'Укажите возрастной интервал в формате: "20 - 40".\n' \
                   f'(Минимальный возраст - 16 лет, максимальный - 99)'
        if self.search_params.get('age_to') is None:
            return f'Укажите возрастной интервал в формате: "20 - 40".\n' \
                   f'(Минимальный возраст - 16 лет, максимальный - 99)'
        self.check_age_params()
        return f'Все параметры заданы:\n' \
               f'{"мужчина" if self.search_params["gender"] == "М" else "женщина"},' \
               f' возраст: {self.search_params["age_from"]} - ' \
               f'{self.search_params["age_to"]}, {self.search_params["city"]}' \
               f'\n\nНачинаю поиск... Дождитесь ответа.'

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
