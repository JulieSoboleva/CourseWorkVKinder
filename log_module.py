import logging
import sys


def logger(path):
    logging.basicConfig(level=logging.INFO, filename=path, filemode='w',
                        format='%(asctime)s %(levelname)s %(message)s',
                        force=True, encoding='utf-8')

    def __logger(old_function):

        def new_function(*args, **kwargs):
            logging.info(f'Вызвана функция {old_function.__name__} '
                         f'с аргументами {args} и {kwargs}')
            try:
                result = old_function(*args, **kwargs)
                logging.info(f'Результат: {result}')
                return result
            except Exception:
                error = sys.exc_info()[1]
                result = f'Ошибка: {error.args[0]}'
                logging.info(f'Результат: {result}')
                return f'{result}\nКажется я сломался...\n' \
                       f'Начнем сначала? Наберите "запрос".'
        return new_function
    return __logger
