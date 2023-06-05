import socket
import json
import sys
from utils import get_msg, send_msg
from logs.decor_log import log
import logging
import logs.client_log_config
import argparse
import time
import threading
from metaclasses import ClientVerifier
from client_db import ClientDB

sys.setrecursionlimit(10000)
logger = logging.getLogger('client')
sock_lock = threading.Lock()
database_lock = threading.Lock()

class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()


    '''выход'''
    def create_exit_message(self):
        return {
            "action": "exit",
            "time": time.time(),
            "user": self.account_name
        }


    
    def create_message(self):
        """
        Функция запрашивает кому отправить сообщение и само сообщение,
        и отправляет полученные данные на сервер
        """
        to_user = input('Введите получателя сообщения: ')
        message = input('Введите сообщение для отправки: ')
        message_dict = {
            'action': 'message',
            'from': self.account_name,
            'to_user': to_user,
            'time': time.time(),
            'msg_text': message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')
        # Сохраняем сообщения для истории
        with database_lock:
            self.database.save_message(self.account_name , to_user , message)
        with sock_lock:
            try:
                send_msg(self.sock, message_dict)
                logger.info(f'Отправлено сообщение для пользователя {to_user}')
            except:
                logger.critical('Потеряно соединение с сервером.')
                exit(1)


    
    def run(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'exit':
                with sock_lock:
                    try:
                        send_msg(self.sock, self.create_exit_message())
                    except:
                        pass
                    print('Завершение соединения.')
                    logger.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            # Редактирование контактов
            elif command == 'edit':
                self.edit_contacts()
            # Список контактов
            elif command == 'contacts':
                with database_lock:
                    contacts_list = self.database.get_contacts()
                for contact in contacts_list:
                    print(contact)
            else:
                print('Команда не распознана')


    def print_help(self):
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('contacts - список контактов')
        print('edit - редактирование списка контактов')
        print('exit - выход из программы')

    # Функция изменеия контактов
    def edit_contacts(self):
        ans = input('Для удаления введите del, для добавления add: ')
        if ans == 'del':
            edit = input('Введите имя удаляемного контакта: ')
            with database_lock:
                if self.database.check_contact(edit):
                    self.database.del_contact(edit)
                else:
                    logger.error('Попытка удаления несуществующего контакта.')
        elif ans == 'add':
            # Проверка на возможность такого контакта
            edit = input('Введите имя создаваемого контакта: ')
            if self.database.check_user(edit):
                with database_lock:
                    self.database.add_contact(edit)
                with sock_lock:
                    add_contact(self.sock, self.account_name, edit)


class ClientReader(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock, database):
        self.account_name = account_name
        self.sock = sock
        self.database = database
        super().__init__()


    
    def run(self):
        """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
        while True:
            time.sleep(1)
            with sock_lock:
                try:
                    message = get_msg(self.sock)
                    if 'action' in message and message['action'] == 'message' and \
                            'from' in message and 'to_user' in message \
                            and 'msg_text' in message and message['to_user'] == self.account_name:
                        print(f'\nПолучено сообщение от пользователя {message["from"]}:'
                            f'\n{message["msg_text"]}')
                        logger.info(f'Получено сообщение от пользователя {message["from"]}:'
                                    f'\n{message["msg_text"]}')
                        with database_lock:
                            try:
                                self.database.save_message(message['from'], self.account_name, message["msg_text"])
                            except:
                                logger.error('Ошибка взаимодействия с базой данных')
                    else:
                        logger.error(f'Получено некорректное сообщение с сервера: {message}')
                except (OSError, ConnectionError, ConnectionAbortedError,
                        ConnectionResetError, json.JSONDecodeError):
                    logger.critical(f'Потеряно соединение с сервером.')
                    break

# Функция добавления пользователя в контакт лист
def add_contact(sock, username, contact):
    logger.debug(f'Создание контакта {contact}')
    req = {
        'action': 'add_contact',
        'time': time.time(),
        'user': username,
        'contact': contact
    }
    send_msg(sock, req)
    ans = get_msg(sock)
    if 'response' in ans and ans['response'] == 200:
        pass
    else:
        return f'Ошибка создания контакта'
    print('Удачное создание контакта.')
    
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
def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default='127.0.0.1', nargs='?')
    parser.add_argument('port', default=7777, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    my_address = namespace.addr
    my_port = namespace.port
    client_name = namespace.name
    return my_address, my_port, client_name

# Функция запроса списка известных пользователей
def user_list_request(sock, username):
    logger.debug(f'Запрос списка известных пользователей {username}')
    req = {
        'action': 'get_users',
        'time': time.time(),
        'user': username
    }
    send_msg(sock, req)
    ans = get_msg(sock)
    if 'response' in ans and ans['response'] == 202:
        return ans['data_list']
    else:
        return f'ServerError'
    
# Функция запрос контакт листа
def contacts_list_request(sock, name):
    logger.debug(f'Запрос контакт листа для пользователся {name}')
    req = {
        'action': 'get_contacts',
        'time': time.time(),
        'user': name
    }
    logger.debug(f'Сформирован запрос {req}')
    send_msg(sock, req)
    ans = get_msg(sock)
    logger.debug(f'Получен ответ {ans}')
    if 'response' in ans and ans['response'] == 202:
        return ans['data_list']
    else:
        return f'ServerError'    

def database_load(sock, database, username):
    # Загружаем список известных пользователей
    users_list = user_list_request(sock, username)
    database.add_users(users_list)

    # Загружаем список контактов
    contacts_list = contacts_list_request(sock, username)
    for contact in contacts_list:
        database.add_contact(contact)

def main_client():
    my_address, my_port, client_name = create_arg_parser()
    try:
        if my_port < 1024 or my_port > 65535:
            raise ValueError
    except IndexError:
        my_address = '127.0.0.1'
        my_port = 7777
    except ValueError:
        logger.critical(f'Указан не верный порт!!! Порт не может быть меньше "1024" или больше "65535"')
        exit(1)
    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Запущен клиент с парамертами: адрес сервера: {my_address}, '
        f'порт: {my_port}, имя пользователя: {client_name}')
        logger.info(
        f'Запущен клиент с парамертами: адрес сервера: {my_address}, '
        f'порт: {my_port}, имя пользователя: {client_name}')
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Создать сокет TCP
        time.sleep(1)
        s.connect((my_address, my_port)) # Соединиться с сервером
        send_msg(s, create_presence(client_name))
        answer = get_msg(s)
        logger.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        logger.error('Не удалось декодировать полученную Json строку.')
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        logger.critical(
            f'Не удалось подключиться к серверу {my_address}:{my_port}, '
            f'конечный компьютер отверг запрос на подключение.')
        exit(1)
    else:
        database = ClientDB(client_name)
        database_load(s, database, client_name)
    # Если соединение с сервером установлено корректно,
    # запускаем клиенский процесс приёма сообщний
        receiver = ClientReader(client_name, s, database)
        receiver.daemon = True
        receiver.start()
    # затем запускаем отправку сообщений и взаимодействие с пользователем.
        user_interface = ClientSender(client_name, s, database)
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