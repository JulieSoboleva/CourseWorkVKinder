from bot import VK_Bot
from random import randrange
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from logic.service import Service
from config import group_token
from log_module import logger

vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)
bots_dict = {}


@logger(path='bot.log')
def start_listener():
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                if bots_dict.get(event.user_id) is None:
                    bots_dict[event.user_id] = VK_Bot(event.user_id, vk)
                write_msg(event.user_id,
                          bots_dict[event.user_id].new_message(event.text),
                          attachment=bots_dict[event.user_id].attachment,
                          keyboard=bots_dict[event.user_id].keyboard)
                if bots_dict[event.user_id].stop:
                    break
                if ready_to_search(event.user_id):
                    write_msg(event.user_id,
                              bots_dict[event.user_id].find_candidates(),
                              attachment=bots_dict[event.user_id].attachment,
                              keyboard=bots_dict[event.user_id].keyboard)


@logger(path='bot.log')
def write_msg(user_id, message, attachment, keyboard):
    post = {
        'user_id': user_id,
        'message': message,
        'random_id': randrange(10 ** 7)
    }
    if keyboard is not None:
        post['keyboard'] = keyboard.get_keyboard()
    if attachment is not None:
        post['attachment'] = ','.join(attachment)
    vk.method('messages.send', post)


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
    # service.drop_tables()
    service.create_tables()
    start_listener()
    service.session.close()
