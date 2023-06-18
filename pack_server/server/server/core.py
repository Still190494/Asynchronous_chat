import threading
import logging
import select
import socket
import json
import hmac
import binascii
import os

from logs.decor_log import log
from utils.metaclasses import ServerVerifier
from utils.descriptors import DescriptPort
from utils.utils import send_msg, get_msg
from utils.login_required import login_required

# Загрузка логера
logger = logging.getLogger('server')


class MessageProcessor(threading.Thread):
    """Класс Сервер"""
    port = DescriptPort()

    def __init__(self, listen_address, listen_port, database):
        # Параментры подключения
        self.addr = listen_address
        self.port = listen_port

        # База данных сервера
        self.database = database

        # Сокет, через который будет осуществляться работа
        self.sock = None

        # Список подключённых клиентов.
        self.clients = []

        # Сокеты
        self.listen_sockets = None
        self.error_sockets = None

        # Флаг продолжения работы
        self.running = True

        # Словарь содержащий сопоставленные имена и соответствующие им сокеты.
        self.names = dict()

        # Конструктор предка
        super().__init__()

    def run(self):
        """Метод обрабатывающий взаимодействие клиентов с сервером"""
        # Инициализация Сокета
        self.init_socket()

        # Основной цикл программы сервера
        while self.running:
            # Ждём подключения, если таймаут вышел, ловим исключение.
            try:
                client, client_address = self.sock.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соедение с ПК {client_address}')
                client.settimeout(5)
                self.clients.append(client)

            recv_data_lst = []
            send_data_lst = []
            err_lst = []
            # Проверяем на наличие ждущих клиентов
            try:
                if self.clients:
                    recv_data_lst, self.listen_sockets, self.error_sockets = select.select(
                        self.clients, self.clients, [], 0)
            except OSError as err:
                logger.error(f'Ошибка работы с сокетами: {err.errno}')

            # принимаем сообщения и если ошибка, исключаем клиента.
            if recv_data_lst:
                for client_with_message in recv_data_lst:
                    try:
                        self.process_client_message(
                            get_msg(client_with_message), client_with_message)
                    except (OSError, json.JSONDecodeError, TypeError) as err:
                        logger.debug(f'Getting data from client exception.', exc_info=err)
                        self.remove_client(client_with_message)

    def remove_client(self, client):
        """Метод отключения пользователя"""
        logger.info(f'Клиент {client.getpeername()} отключился от сервера.')
        for name in self.names:
            if self.names[name] == client:
                self.database.user_logout(name)
                del self.names[name]
                break
        self.clients.remove(client)
        client.close()

    def init_socket(self):
        """Метод создания сокета"""
        logger.info(
            f'Запущен сервер, порт для подключений: {self.port} , адрес с которого принимаются подключения: {self.addr}. Если адрес не указан, принимаются соединения с любых адресов.')
        # Готовим сокет
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.bind((self.addr, self.port))
        transport.settimeout(0.5)

        # Начинаем слушать сокет.
        self.sock = transport
        self.sock.listen()

    def process_message(self, message):
        """Метод отправки сообщений пользователям"""
        if message['to'] in self.names and self.names[message['to']
        ] in self.listen_sockets:
            try:
                send_msg(self.names[message['to']], message)
                logger.info(
                    f'Отправлено сообщение пользователю {message["to"]} от пользователя {message["from"]}.')
            except OSError:
                self.remove_client(message['to'])
        elif message['to'] in self.names and self.names[message['to']] not in self.listen_sockets:
            logger.error(
                f'Связь с клиентом {message["to"]} была потеряна. Соединение закрыто, доставка невозможна.')
            self.remove_client(self.names[message['to']])
        else:
            logger.error(
                f'Пользователь {message["to"]} не зарегистрирован на сервере, отправка сообщения невозможна.')

    @login_required
    def process_client_message(self, message, client):
        """Метод обрабатывающий полученные сообщения от клиентов"""
        logger.debug(f'Разбор сообщения от клиента : {message}')
        # Если это сообщение о присутствии, принимаем и отвечаем
        if 'action' in message and message['action'] == 'presence' and 'time' in message and 'user' in message:
            # Если сообщение о присутствии то вызываем функцию авторизации.
            self.autorize_user(message, client)

        # Если это сообщение, то отправляем его получателю.
        elif 'action' in message and message['action'] == 'message' and 'to' in message and 'time' in message \
                and 'from' in message and 'mess_text' in message and self.names[message['from']] == client:
            if message['to'] in self.names:
                self.database.process_message(
                    message['from'], message['to'])
                self.process_message(message)
                try:
                    resp_ok = {'response': 200}
                    send_msg(client, resp_ok)
                except OSError:
                    self.remove_client(client)
            else:
                response = {"response": 400,
                            "error": 'Пользователь не зарегистрирован на сервере'}
                try:
                    send_msg(client, response)
                except OSError:
                    pass
            return

        # Если клиент выходит
        elif 'action' in message and message['action'] == 'exit' and 'account_name' in message \
                and self.names[message['account_name']] == client:
            self.remove_client(client)

        # Если это запрос контакт-листа
        elif 'action' in message and message['action'] == 'get_contacts' and 'user' in message and \
                self.names[message['user']] == client:
            response = {'response': 202,
                        'data_list': self.database.get_contacts(message['user'])}
            try:
                send_msg(client, response)
            except OSError:
                self.remove_client(client)

        # Если это добавление контакта
        elif 'action' in message and message['action'] == 'add' and 'account_name' in message and 'user' in message \
                and self.names[message['user']] == client:
            self.database.add_contact(message['user'], message['account_name'])
            try:
                resp_ok = {'response': 200}
                send_msg(client, resp_ok)
            except OSError:
                self.remove_client(client)

        # Если это удаление контакта
        elif 'action' in message and message['action'] == 'remove' and 'account_name' in message and 'user' in message \
                and self.names[message['user']] == client:
            self.database.remove_contact(message['user'], message['account_name'])
            try:
                resp_ok = {'response': 200}
                send_msg(client, resp_ok)
            except OSError:
                self.remove_client(client)

        # Если это запрос известных пользователей
        elif 'action' in message and message['action'] == 'get_users' and 'account_name' in message \
                and self.names[message['account_name']] == client:
            response = {'response': 202, 'data_list': [user[0] for user in self.database.users_list()]}
            try:
                send_msg(client, response)
            except OSError:
                self.remove_client(client)

        # Если это запрос публичного ключа пользователя
        elif 'action' in message and message['action'] == 'pubkey_need' and 'account_name' in message:
            response = {'response': 511,
                        'bin': self.database.get_pubkey(message['account_name'])}
            # может быть, что ключа ещё нет (пользователь никогда не логинился,
            # тогда шлём 400)
            if response['bin']:
                try:
                    send_msg(client, response)
                except OSError:
                    self.remove_client(client)
            else:
                response = {"response": 400,
                            "error": 'Нет публичного ключа для данного пользователя'}
                try:
                    send_msg(client, response)
                except OSError:
                    self.remove_client(client)

        # Иначе отдаём Bad request
        else:
            response = {"response": 400,
                        "error": 'Запрос некорректен.'}
            try:
                send_msg(client, response)
            except OSError:
                self.remove_client(client)

    def autorize_user(self, message, sock):
        """Метод авторизации пользователей"""
        # Если имя пользователя уже занято то возвращаем 400
        logger.debug(f'Start auth process for {message["user"]}')
        if message['user']['account_name'] in self.names.keys():
            response = {"response": 400,
                        "error": 'Имя пользователя уже занято.'}
            try:
                logger.debug(f'Username busy, sending {response}')
                send_msg(sock, response)
            except OSError:
                logger.debug('OS Error')
                pass
            self.clients.remove(sock)
            sock.close()
        # Проверяем что пользователь зарегистрирован на сервере.
        elif not self.database.check_user(message['user']['account_name']):
            response = {"response": 400,
                        "error": 'Пользователь не зарегистрирован.'}
            try:
                logger.debug(f'Unknown username, sending {response}')
                send_msg(sock, response)
            except OSError:
                pass
            self.clients.remove(sock)
            sock.close()
        else:
            logger.debug('Correct username, starting passwd check.')
            # Иначе отвечаем 511 и проводим процедуру авторизации
            # Словарь - заготовка
            message_auth = {'response': 511,
                            'bin': None
                            }
            # Набор байтов в hex представлении
            random_str = binascii.hexlify(os.urandom(64))
            # В словарь байты нельзя, декодируем (json.dumps -> TypeError)
            message_auth['bin'] = random_str.decode('ascii')
            # Создаём хэш пароля и связки с рандомной строкой, сохраняем
            # серверную версию ключа
            hash = hmac.new(self.database.get_hash(message['user']['account_name']), random_str, 'MD5')
            digest = hash.digest()
            logger.debug(f'Auth message = {message_auth}')
            try:
                # Обмен с клиентом
                send_msg(sock, message_auth)
                ans = get_msg(sock)
            except OSError as err:
                logger.debug('Error in auth, data:', exc_info=err)
                sock.close()
                return
            client_digest = binascii.a2b_base64(ans['bin'])
            # Если ответ клиента корректный, то сохраняем его в список
            # пользователей.
            if 'response' in ans and ans['response'] == 511 and hmac.compare_digest(
                    digest, client_digest):
                self.names[message['user']['account_name']] = sock
                client_ip, client_port = sock.getpeername()
                try:
                    resp_ok = {'response': 200}
                    send_msg(sock, resp_ok)
                except OSError:
                    self.remove_client(message['user']['account_name'])
                # добавляем пользователя в список активных и если у него изменился открытый ключ
                # сохраняем новый
                self.database.user_login(
                    message['user']['account_name'],
                    client_ip,
                    client_port,
                    message['user']['pubkey'])
            else:
                response = {"response": 400,
                            "error": 'Неверный пароль.'}
                try:
                    send_msg(sock, response)
                except OSError:
                    pass
                self.clients.remove(sock)
                sock.close()

    def service_update_lists(self):
        """Метод реализующий отправку сервисного сообщения 205 клиентам."""
        for client in self.names:
            try:
                response = {"response": 205}
                send_msg(self.names[client], response)
            except OSError:
                self.remove_client(self.names[client])
