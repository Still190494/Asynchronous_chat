from socket import *
import json
import sys
from utils import get_msg, send_msg, create_exit_message
from logs.decor_log import log
import logging
import logs.client_log_config
import argparse
import time
import threading


sys.setrecursionlimit(10000)
logger = logging.getLogger('client')

@log
def create_presence(account_name):
    """Функция генерирует запрос о присутствии клиента"""
    out = {
        "action": "presence",
        "time": time.time(),
        "user": account_name
    }
    logger.info(f'Сформировано сообщение для пользователя {account_name}')
    return out

@log
def message_from_server(sock, my_username):
    """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
    while True:
        try:
            message = get_msg(sock)
            if 'action' in message and message['action'] == 'message' and \
                    'from' in message and 'to_user' in message \
                    and 'msg_text' in message and message['to_user'] == my_username:
                print(f'\nПолучено сообщение от пользователя {message["from"]}:'
                      f'\n{message["msg_text"]}')
                logger.info(f'Получено сообщение от пользователя {message["from"]}:'
                            f'\n{message["msg_text"]}')
            else:
                logger.error(f'Получено некорректное сообщение с сервера: {message}')
        except (OSError, ConnectionError, ConnectionAbortedError,
                ConnectionResetError, json.JSONDecodeError):
            logger.critical(f'Потеряно соединение с сервером.')
            break

@log
def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default='127.0.0.1', nargs='?')
    parser.add_argument('port', default=7777, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    return parser

@log
def create_message(sock, account_name='admin'):
    """
    Функция запрашивает кому отправить сообщение и само сообщение,
    и отправляет полученные данные на сервер
    :param sock:
    :param account_name:
    :return:
    """
    to_user = input('Введите получателя сообщения: ')
    message = input('Введите сообщение для отправки: ')
    message_dict = {
        'action': 'message',
        'from': account_name,
        'to_user': to_user,
        'time': time.time(),
        'msg_text': message
    }
    logger.debug(f'Сформирован словарь сообщения: {message_dict}')
    try:
        send_msg(sock, message_dict)
        logger.info(f'Отправлено сообщение для пользователя {to_user}')
    except:
        logger.critical('Потеряно соединение с сервером.')
        sys.exit(1)

@log
def user_interactive(sock, username):
    while True:
        command = input('Введите команду: message(написаль сообщение) или exit(выйти) ')
        if command == 'message':
            create_message(sock, username)
        elif command == 'exit':
            send_msg(sock, create_exit_message(username))
            print('Завершение соединения.')
            logger.info('Завершение работы по команде пользователя.')
            # Задержка неоходима, чтобы успело уйти сообщение о выходе
            time.sleep(0.5)
            break
        else:
            print('Команда не распознана')


def main_client():
    parser = create_arg_parser()
    namespace = parser.parse_args(sys.argv[1:])
    try:
        my_address = namespace.addr
        my_port = namespace.port
        client_name = namespace.name
        if my_port < 1024 or my_port > 65535:
            raise ValueError
    except IndexError:
        my_address = '127.0.0.1'
        my_port = 7777
    except ValueError:
        logger.critical(f'Указан не верный порт!!! Порт не может быть меньше "1024" или больше "65535"')
        sys.exit(1)
    if not client_name:
        client_name = input('Введите имя пользователя: ')
    try:
        s = socket(AF_INET, SOCK_STREAM) # Создать сокет TCP
        s.connect((my_address, my_port)) # Соединиться с сервером
        send_msg(s, create_presence(client_name))
        answer = get_msg(s)
        logger.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
        print(f'Запущен клиент с парамертами: адрес сервера: {my_address}, '
        f'порт: {my_port}, имя пользователя: {client_name}')
        logger.info(
        f'Запущен клиент с парамертами: адрес сервера: {my_address}, '
        f'порт: {my_port}, имя пользователя: {client_name}')
    except json.JSONDecodeError:
        logger.error('Не удалось декодировать полученную Json строку.')
        sys.exit(1)
    except (ConnectionRefusedError, ConnectionError):
        logger.critical(
            f'Не удалось подключиться к серверу {my_address}:{my_port}, '
            f'конечный компьютер отверг запрос на подключение.')
        sys.exit(1)
    else:
    # Если соединение с сервером установлено корректно,
    # запускаем клиенский процесс приёма сообщний
        receiver = threading.Thread(target=message_from_server, args=(s, client_name))
        receiver.daemon = True
        receiver.start()
    # затем запускаем отправку сообщений и взаимодействие с пользователем.
        user_interface = threading.Thread(target=user_interactive, args=(s, client_name))
        user_interface.daemon = True
        user_interface.start()
        logger.debug('Запущены процессы')
        while True:
            time.sleep(1)
            if receiver.is_alive() and user_interface.is_alive():
                continue
            break

    

if __name__ == '__main__':
    main_client()