from bot import VK_Bot
from random import randrange
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from logic.service import Service
from config import group_token

vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)
bots_dict = {}


def start_listener():
    print("Сервер запущен")
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                if bots_dict.get(event.user_id) is None:
                    bots_dict[event.user_id] = VK_Bot(event.user_id, vk)

                write_msg(event.user_id,
                          bots_dict[event.user_id].new_message(event.text))
                print('Текст: ', event.text)
                if ready_to_search(event.user_id):
                    bots_dict[event.user_id].get_candidates_list()
                    bots_dict[event.user_id].search_params = {}


def write_msg(user_id, message):
    vk.method('messages.send', {'user_id': user_id,
                                'message': message,
                                'random_id': randrange(10 ** 7)})


def ready_to_search(user_id) -> bool:
    if bots_dict[user_id].search_params.get('gender') is None:
        return False
    if bots_dict[user_id].search_params.get('city') is None:
        return False
    if bots_dict[user_id].search_params.get('age_from') is None:
        return False
    if bots_dict[user_id].search_params.get('age_to') is None:
        return False
    return True


if __name__ == '__main__':
    service = Service()
    service.recreate_tables()
    start_listener()
    service.session.close_all()
