import socket
import sys
import time
import logging
import json
import hashlib
import hmac
import binascii
import threading
from PyQt5.QtCore import pyqtSignal, QObject


from Asynchronous_chat.utils import *

from Asynchronous_chat.errors import ServerError

# Логер и объект блокировки для работы с сокетом.
logger = logging.getLogger('client')
socket_lock = threading.Lock()


# Класс - Транспорт, отвечает за взаимодействие с сервером
class ClientTransport(threading.Thread, QObject):
    # Сигналы новое сообщение и потеря соединения
    new_message = pyqtSignal(dict)
    message_205 = pyqtSignal()
    connection_lost = pyqtSignal()

    def __init__(self, port, ip_address, database, username, passwd, keys):
        # Вызываем конструктор предка
        threading.Thread.__init__(self)
        QObject.__init__(self)

        # Класс База данных - работа с базой
        self.database = database
        # Имя пользователя
        self.username = username
        # Пароль
        self.password = passwd
        # Сокет для работы с сервером
        self.transport = None
        # Набор ключей для шифрования
        self.keys = keys
        # Устанавливаем соединение:
        self.connection_init(port, ip_address)
        # Обновляем таблицы известных пользователей и контактов
        try:
            self.user_list_update()
            self.contacts_list_update()
        except OSError as err:
            if err.errno:
                logger.critical(f'Потеряно соединение с сервером.')
                raise ServerError('Потеряно соединение с сервером!')
            logger.error('Timeout соединения при обновлении списков пользователей.')
        except json.JSONDecodeError:
            logger.critical(f'Потеряно соединение с сервером.')
            raise ServerError('Потеряно соединение с сервером!')
            # Флаг продолжения работы транспорта.
        self.running = True

    # Функция инициализации соединения с сервером
    def connection_init(self, port, ip):
        # Инициализация сокета и сообщение серверу о нашем появлении
        self.transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Таймаут необходим для освобождения сокета.
        self.transport.settimeout(5)

        # Соединяемся, 5 попыток соединения, флаг успеха ставим в True если удалось
        connected = False
        for i in range(5):
            logger.info(f'Попытка подключения №{i + 1}')
            try:
                self.transport.connect((ip, port))
            except (OSError, ConnectionRefusedError):
                pass
            else:
                connected = True
                break
            time.sleep(1)

        # Если соединится не удалось - исключение
        if not connected:
            logger.critical('Не удалось установить соединение с сервером')
            raise ServerError('Не удалось установить соединение с сервером')

        logger.debug('Установлено соединение с сервером')

        # Запускаем процедуру авторизации
        # Получаем хэш пароля
        passwd_bytes = self.password.encode('utf-8')
        salt = self.username.lower().encode('utf-8')
        passwd_hash = hashlib.pbkdf2_hmac('sha512', passwd_bytes, salt, 10000)
        passwd_hash_string = binascii.hexlify(passwd_hash)

        logger.debug(f'Passwd hash ready: {passwd_hash_string}')

        # Посылаем серверу приветственное сообщение и получаем ответ что всё нормально или ловим исключение.

        try:
            with socket_lock:
                send_msg(self.transport, self.create_presence())
                ans = get_msg(self.transport)
                logger.debug(f'Ответ сервера = {ans}.')
                # Если сервер вернул ошибку, бросаем исключение.
                if 'response' in ans:
                    if ans['response'] == 400:
                        raise ServerError(ans['error'])
                    elif ans['response'] == 511:
                        # Если всё нормально, то продолжаем процедуру
                        # авторизации.
                        ans_data = ans['bin']
                        hash = hmac.new(passwd_hash_string, ans_data.encode('utf-8'), 'MD5')
                        digest = hash.digest()
                        my_ans = {'response': 511}
                        my_ans['bin'] = binascii.b2a_base64(
                            digest).decode('ascii')
                        send_msg(self.transport, my_ans)
                        self.process_server_ans(get_msg(self.transport))
        except (OSError, json.JSONDecodeError):
            logger.critical('Потеряно соединение с сервером!')
            raise ServerError('Потеряно соединение с сервером!')

        # Раз всё хорошо, сообщение о установке соединения.
        logger.info('Соединение с сервером успешно установлено.')

    # Функция, генерирующая приветственное сообщение для сервера

    def create_presence(self):
        """Функция генерирует запрос о присутствии клиента"""
        # Получаем публичный ключ и декодируем его из байтов
        pubkey = self.keys.publickey().export_key().decode('ascii')
        out = {
            'action': 'presence',
            'time': time.time(),
            'user': {
                'account_name': self.username,
                'pubkey': pubkey
            }
        }
        logger.info(f'Сформировано сообщение пользователя {self.username}')
        return out

    # Функция обрабатывающяя сообщения от сервера. Ничего не возращает. Генерирует исключение при ошибке.
    def process_server_ans(self, message):
        logger.debug(f'Разбор сообщения от сервера: {message}')

        # Если это подтверждение чего-либо
        if 'response' in message:
            if message['response'] == 200:
                return
            elif message['response'] == 400:
                raise ServerError(f'{message["error"]}')
            elif message['response'] == 205:
                self.user_list_update()
                self.contacts_list_update()
                self.message_205.emit()
            else:
                logger.debug(f'Принят неизвестный код подтверждения {message["response"]}')

        # Если это сообщение от пользователя добавляем в базу, даём сигнал о новом сообщении
        elif 'action' in message and message['action'] == 'message' and 'from' in message and 'to' in message \
                and 'mess_text' in message and message['to'] == self.username:
            logger.debug(f'Получено сообщение от пользователя {message["from"]}:{message["mess_text"]}')
            # self.database.save_message(message['from'] , 'in' , message["mess_text"])
            self.new_message.emit(message['from'])


    # Функция обновляющая контакт - лист с сервера
    def contacts_list_update(self):
        logger.debug(f'Запрос контакт листа для пользователся {self.name}')
        req = {
            'action': 'get_contacts',
            'time': time.time(),
            'user': self.username
        }
        logger.debug(f'Сформирован запрос {req}')
        with socket_lock:
            send_msg(self.transport, req)
            ans = get_msg(self.transport)
        logger.debug(f'Получен ответ {ans}')
        if 'response' in ans and ans['response'] == 202:
            for contact in ans['data_list']:
                self.database.add_contact(contact)
        else:
            logger.error('Не удалось обновить список контактов.')

    # Функция обновления таблицы известных пользователей.
    def user_list_update(self):
        logger.debug(f'Запрос списка известных пользователей {self.username}')
        req = {
            'action': 'get_users',
            'time': time.time(),
            'account_name': self.username
        }
        with socket_lock:
            send_msg(self.transport, req)
            ans = get_msg(self.transport)
        if 'response' in ans and ans['response'] == 202:
            self.database.add_users(ans['data_list'])
        else:
            logger.error('Не удалось обновить список известных пользователей.')


    def key_request(self, user):
        '''Метод запрашивающий с сервера публичный ключ пользователя.'''
        logger.debug(f'Запрос публичного ключа для {user}')
        req = {
            'action': 'pubkey_need',
            'time': time.time(),
            'account_name': user
        }
        with socket_lock:
            send_msg(self.transport, req)
            ans = get_msg(self.transport)
        if 'response' in ans and ans['response'] == 511:
            return ans['bin']
        else:
            logger.error(f'Не удалось получить ключ собеседника{user}.')
    # Функция сообщающая на сервер о добавлении нового контакта
    def add_contact(self, contact):
        logger.debug(f'Создание контакта {contact}')
        req = {
            'action': 'add',
            'time': time.time(),
            'user': self.username,
            'account_name': contact
        }
        with socket_lock:
            send_msg(self.transport, req)
            self.process_server_ans(get_msg(self.transport))

    # Функция удаления клиента на сервере
    def remove_contact(self, contact):
        logger.debug(f'Удаление контакта {contact}')
        req = {
            'action': 'remove',
            'time': time.time(),
            'user': self.username,
            'account_name': contact
        }
        with socket_lock:
            send_msg(self.transport, req)
            self.process_server_ans(get_msg(self.transport))

    # Функция закрытия соединения, отправляет сообщение о выходе.
    def transport_shutdown(self):
        self.running = False
        message = {
            'action': 'exit',
            'time': time.time(),
            'account_name': self.username
        }
        with socket_lock:
            try:
                send_msg(self.transport, message)
            except OSError:
                pass
        logger.debug('Транспорт завершает работу.')
        time.sleep(0.5)

    # Функция отправки сообщения на сервер
    def send_message(self, to, message):
        message_dict = {
            'action': 'message',
            'from': self.username,
            'to': to,
            'time': time.time(),
            'mess_text': message
        }
        logger.debug(f'Сформирован словарь сообщения: {message_dict}')

        # Необходимо дождаться освобождения сокета для отправки сообщения
        with socket_lock:
            send_msg(self.transport, message_dict)
            self.process_server_ans(get_msg(self.transport))
            logger.info(f'Отправлено сообщение для пользователя {to}')

    def run(self):
        logger.debug('Запущен процесс - приёмник собщений с сервера.')
        while self.running:
            # Отдыхаем секунду и снова пробуем захватить сокет.
            # если не сделать тут задержку, то отправка может достаточно долго ждать освобождения сокета.
            time.sleep(1)
            message = None
            with socket_lock:
                try:
                    self.transport.settimeout(0.5)
                    message = get_msg(self.transport)
                except OSError as err:
                    if err.errno:
                        logger.critical(f'Потеряно соединение с сервером.')
                        self.running = False
                        self.connection_lost.emit()
                # Проблемы с соединением
                except (ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError, TypeError):
                    logger.debug(f'Потеряно соединение с сервером.')
                    self.running = False
                    self.connection_lost.emit()
                # Если сообщение получено, то вызываем функцию обработчик:
                else:
                    logger.debug(f'Принято сообщение с сервера: {message}')
                    self.process_server_ans(message)
                finally:
                    self.transport.settimeout(5)
