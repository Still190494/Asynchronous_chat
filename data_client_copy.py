
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


sys.setrecursionlimit(10000)
logger = logging.getLogger('client')




class ClientSender(threading.Thread, metaclass=ClientVerifier):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    # Функция создаёт словарь с сообщением о выходе.
    def create_exit_message(self):
        return {
            "action": "exit",
            "time": time.time(),
            "user": self.account_name
        }

    # Функция запрашивает кому отправить сообщение и само сообщение, и отправляет полученные данные на сервер.
    def create_message(self):
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
        try:
            send_msg(self.sock, message_dict)
            logger.info(f'Отправлено сообщение для пользователя {to_user}')
        except:
            logger.critical('Потеряно соединение с сервером.')
            exit(1)

    # Функция взаимодействия с пользователем, запрашивает команды, отправляет сообщения
    def run(self):
        self.print_help()
        while True:
            command = input('Введите команду: ')
            if command == 'message':
                self.create_message()
            elif command == 'help':
                self.print_help()
            elif command == 'exit':
                try:
                    send_msg(self.sock, self.create_exit_message())
                except:
                    pass
                print('Завершение соединения.')
                logger.info('Завершение работы по команде пользователя.')
                # Задержка неоходима, чтобы успело уйти сообщение о выходе
                time.sleep(0.5)
                break
            else:
                print('Команда не распознана, попробойте снова. help - вывести поддерживаемые команды.')

    # Функция выводящяя справку по использованию.
    def print_help(self):
        print('Поддерживаемые команды:')
        print('message - отправить сообщение. Кому и текст будет запрошены отдельно.')
        print('help - вывести подсказки по командам')
        print('exit - выход из программы')


# Класс-приёмник сообщений с сервера. Принимает сообщения, выводит в консоль.
class ClientReader(threading.Thread , metaclass=ClientVerifier):
    def __init__(self, account_name, sock):
        self.account_name = account_name
        self.sock = sock
        super().__init__()

    # Основной цикл приёмника сообщений, принимает сообщения, выводит в консоль. Завершается при потере соединения.
    def run(self):
        while True:
            try:
                message = get_msg(self.sock)
                if 'action' in message and message['action'] == 'message' and \
                        'from' in message and 'to_user' in message \
                        and 'msg_text' in message and message['to_user'] == self.account_name:
                    print(f'\nПолучено сообщение от пользователя {message["from"]}:'
                        f'\n{message["msg_text"]}')
                    logger.info(f'Получено сообщение от пользователя {message["from"]}:'
                                f'\n{message["msg_text"]}')
                else:
                    logger.error(f'Получено некорректное сообщение с сервера: {message}')
            except (OSError, ConnectionError, ConnectionAbortedError, ConnectionResetError, json.JSONDecodeError):
                logger.critical(f'Потеряно соединение с сервером.')
                break


# Функция генерирует запрос о присутствии клиента
@log
def create_presence(account_name):
    out = {
        "action": "presence",
        "time": time.time(),
        "user": account_name
    }
    logger.debug(f'Сформировано сообщение для пользователя {account_name}')
    return out


# Функция разбирает ответ сервера на сообщение о присутствии, возращает 200 если все ОК или генерирует исключение при\
# ошибке.
@log
def process_response_ans(message):
    logger.debug(f'Разбор приветственного сообщения от сервера: {message}')
    if 'response' in message:
        if message['response'] == 200:
            return '200 : OK'
        elif message['response'] == 400:
            return '400 : BAD'
    raise f'В принятом словаре отсутствует обязательное поле'


# Парсер аргументов коммандной строки
@log
def arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default='127.0.0.1', nargs='?')
    parser.add_argument('port', default=7777, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    server_address = namespace.addr
    server_port = namespace.port
    client_name = namespace.name

    # проверим подходящий номер порта
    if not 1023 < server_port < 65536:
        logger.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {server_port}. Допустимы адреса с 1024 до 65535. Клиент завершается.')
        exit(1)

    return server_address, server_port, client_name


def main():
    # Сообщаем о запуске
    print('Консольный месседжер. Клиентский модуль.')

    # Загружаем параметы коммандной строки
    server_address, server_port, client_name = arg_parser()

    # Если имя пользователя не было задано, необходимо запросить пользователя.
    if not client_name:
        client_name = input('Введите имя пользователя: ')
    else:
        print(f'Клиентский модуль запущен с именем: {client_name}')

    logger.info(
        f'Запущен клиент с парамертами: адрес сервера: {server_address} , порт: {server_port}, имя пользователя: {client_name}')

    # Инициализация сокета и сообщение серверу о нашем появлении
    try:
        transport = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        transport.connect((server_address, server_port))
        send_msg(transport, create_presence(client_name))
        answer = process_response_ans(get_msg(transport))
        logger.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
        print(f'Установлено соединение с сервером.')
    except json.JSONDecodeError:
        logger.error('Не удалось декодировать полученную Json строку.')
        exit(1)
    except (ConnectionRefusedError, ConnectionError):
        logger.critical(
            f'Не удалось подключиться к серверу {server_address}:{server_port}, конечный компьютер отверг запрос на подключение.')
        exit(1)
    else:
        # Если соединение с сервером установлено корректно, запускаем клиенский процесс приёма сообщний
        module_reciver = ClientReader(client_name , transport)
        module_reciver.daemon = True
        module_reciver.start()

        # затем запускаем отправку сообщений и взаимодействие с пользователем.
        module_sender = ClientSender(client_name , transport)
        module_sender.daemon = True
        module_sender.start()
        logger.debug('Запущены процессы')

        # Watchdog основной цикл, если один из потоков завершён, то значит или потеряно соединение или пользователь
        # ввёл exit. Поскольку все события обработываются в потоках, достаточно просто завершить цикл.
        while True:
            time.sleep(1)
            if module_reciver.is_alive() and module_sender.is_alive():
                continue
            break


if __name__ == '__main__':
    main()
# class ClientSender(threading.Thread):
#     def __init__(self, account_name, sock):
#         self.account_name = account_name
#         self.sock = sock
#         super().__init__()


#     '''выход'''
#     @log
#     def create_exit_message(self):
#         return {
#             "action": "exit",
#             "time": time.time(),
#             "user": self.account_name
#         }


#     @log
#     def create_message(self):
#         """
#         Функция запрашивает кому отправить сообщение и само сообщение,
#         и отправляет полученные данные на сервер
#         """
#         to_user = input('Введите получателя сообщения: ')
#         message = input('Введите сообщение для отправки: ')
#         message_dict = {
#             'action': 'message',
#             'from': self.account_name,
#             'to_user': to_user,
#             'time': time.time(),
#             'msg_text': message
#         }
#         logger.debug(f'Сформирован словарь сообщения: {message_dict}')
#         try:
#             send_msg(self.sock, message_dict)
#             logger.info(f'Отправлено сообщение для пользователя {to_user}')
#         except:
#             logger.critical('Потеряно соединение с сервером.')
#             exit(1)


#     @log
#     def user_interactive(self):
#         while True:
#             command = input('Введите команду: message(написаль сообщение) или exit(выйти) ')
#             if command == 'message':
#                 self.create_message()
#             elif command == 'exit':
#                 try:
#                     send_msg(self.sock, self.create_exit_message())
#                 except:
#                     pass
#                 print('Завершение соединения.')
#                 logger.info('Завершение работы по команде пользователя.')
#                 # Задержка неоходима, чтобы успело уйти сообщение о выходе
#                 time.sleep(0.5)
#                 break
#             else:
#                 print('Команда не распознана')



# class ClientReader(threading.Thread):
#     def __init__(self, account_name, sock):
#         self.account_name = account_name
#         self.sock = sock
#         super().__init__()


#     @log
#     def message_from_server(self):
#         """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
#         while True:
#             try:
#                 message = get_msg(self.sock)
#                 if 'action' in message and message['action'] == 'message' and \
#                         'from' in message and 'to_user' in message \
#                         and 'msg_text' in message and message['to_user'] == self.account_name:
#                     print(f'\nПолучено сообщение от пользователя {message["from"]}:'
#                         f'\n{message["msg_text"]}')
#                     logger.info(f'Получено сообщение от пользователя {message["from"]}:'
#                                 f'\n{message["msg_text"]}')
#                 else:
#                     logger.error(f'Получено некорректное сообщение с сервера: {message}')
#             except (OSError, ConnectionError, ConnectionAbortedError,
#                     ConnectionResetError, json.JSONDecodeError):
#                 logger.critical(f'Потеряно соединение с сервером.')
#                 break


# @log
# def create_presence(account_name):
#     """Функция генерирует запрос о присутствии клиента"""
#     out = {
#         "action": "presence",
#         "time": time.time(),
#         "user": account_name
#     }
#     logger.info(f'Сформировано сообщение для пользователя {account_name}')
#     return out


# @log
# def create_arg_parser():
#     parser = argparse.ArgumentParser()
#     parser.add_argument('addr', default='127.0.0.1', nargs='?')
#     parser.add_argument('port', default=7777, type=int, nargs='?')
#     parser.add_argument('-n', '--name', default=None, nargs='?')
#     namespace = parser.parse_args(sys.argv[1:])
#     my_address = namespace.addr
#     my_port = namespace.port
#     client_name = namespace.name
#     return my_address, my_port, client_name


# def main_client():
#     my_address, my_port, client_name = create_arg_parser()
#     try:
#         if my_port < 1024 or my_port > 65535:
#             raise ValueError
#     except IndexError:
#         my_address = '127.0.0.1'
#         my_port = 7777
#     except ValueError:
#         logger.critical(f'Указан не верный порт!!! Порт не может быть меньше "1024" или больше "65535"')
#         exit(1)
#     if not client_name:
#         client_name = input('Введите имя пользователя: ')
#     else:
#         print(f'Запущен клиент с парамертами: адрес сервера: {my_address}, '
#         f'порт: {my_port}, имя пользователя: {client_name}')
#         logger.info(
#         f'Запущен клиент с парамертами: адрес сервера: {my_address}, '
#         f'порт: {my_port}, имя пользователя: {client_name}')
#     try:
#         s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Создать сокет TCP
#         s.connect((my_address, my_port)) # Соединиться с сервером
#         send_msg(s, create_presence(client_name))
#         answer = get_msg(s)
#         logger.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
#         print(f'Установлено соединение с сервером.')
#     except json.JSONDecodeError:
#         logger.error('Не удалось декодировать полученную Json строку.')
#         exit(1)
#     except (ConnectionRefusedError, ConnectionError):
#         logger.critical(
#             f'Не удалось подключиться к серверу {my_address}:{my_port}, '
#             f'конечный компьютер отверг запрос на подключение.')
#         exit(1)
#     else:
#     # Если соединение с сервером установлено корректно,
#     # запускаем клиенский процесс приёма сообщний
#         receiver = ClientReader(client_name, s)
#         receiver.daemon = True
#         receiver.start()
#     # затем запускаем отправку сообщений и взаимодействие с пользователем.
#         user_interface = ClientSender(client_name, s)
#         user_interface.daemon = True
#         user_interface.start()
#         logger.debug('Запущены процессы')
#         while True:
#             time.sleep(1)
#             if receiver.is_alive() and user_interface.is_alive():
#                 continue
#             break







# class Client():
#     def __init__(self, my_address, my_port, client_name):
#         self.my_address = my_address
#         self.my_port = my_port
#         self.client_name = client_name


#     @log
#     def create_presence(self, account_name):
#         """Функция генерирует запрос о присутствии клиента"""
#         out = {
#             "action": "presence",
#             "time": time.time(),
#             "user": account_name
#         }
#         logger.info(f'Сформировано сообщение для пользователя {account_name}')
#         return out


#     @log
#     def create_message(self, sock, account_name='admin'):
#         """
#         Функция запрашивает кому отправить сообщение и само сообщение,
#         и отправляет полученные данные на сервер
#         """
#         to_user = input('Введите получателя сообщения: ')
#         message = input('Введите сообщение для отправки: ')
#         message_dict = {
#             'action': 'message',
#             'from': account_name,
#             'to_user': to_user,
#             'time': time.time(),
#             'msg_text': message
#         }
#         logger.debug(f'Сформирован словарь сообщения: {message_dict}')
#         try:
#             send_msg(sock, message_dict)
#             logger.info(f'Отправлено сообщение для пользователя {to_user}')
#         except:
#             logger.critical('Потеряно соединение с сервером.')
#             sys.exit(1)


#     @log
#     def user_interactive(self, sock, username):
#         while True:
#             command = input('Введите команду: message(написаль сообщение) или exit(выйти) ')
#             if command == 'message':
#                 self.create_message(sock, username)
#             elif command == 'exit':
#                 send_msg(sock, create_exit_message(username))
#                 print('Завершение соединения.')
#                 logger.info('Завершение работы по команде пользователя.')
#                 # Задержка неоходима, чтобы успело уйти сообщение о выходе
#                 time.sleep(0.5)
#                 break
#             else:
#                 print('Команда не распознана')


#     @log
#     def message_from_server(self, sock, client_name):
#         """Функция - обработчик сообщений других пользователей, поступающих с сервера"""
#         while True:
#             try:
#                 message = get_msg(sock)
#                 if 'action' in message and message['action'] == 'message' and \
#                         'from' in message and 'to_user' in message \
#                         and 'msg_text' in message and message['to_user'] == client_name:
#                     print(f'\nПолучено сообщение от пользователя {message["from"]}:'
#                         f'\n{message["msg_text"]}')
#                     logger.info(f'Получено сообщение от пользователя {message["from"]}:'
#                                 f'\n{message["msg_text"]}')
#                 else:
#                     logger.error(f'Получено некорректное сообщение с сервера: {message}')
#             except (OSError, ConnectionError, ConnectionAbortedError,
#                     ConnectionResetError, json.JSONDecodeError):
#                 logger.critical(f'Потеряно соединение с сервером.')
#                 break


#     def main_client(self):
#         try:
#             if self.my_port < 1024 or self.my_port > 65535:
#                 raise ValueError
#         except IndexError:
#             self.my_address = '127.0.0.1'
#             self.my_port = 7777
#         except ValueError:
#             logger.critical(f'Указан не верный порт!!! Порт не может быть меньше "1024" или больше "65535"')
#             sys.exit(1)
#         if not self.client_name:
#             self.client_name = input('Введите имя пользователя: ')
#         try:
#             self.s = socket(AF_INET, SOCK_STREAM) # Создать сокет TCP
#             self.s.connect((self.my_address, self.my_port)) # Соединиться с сервером
#             send_msg(self.s, self.create_presence(self.client_name))
#             answer = get_msg(self.s)
#             logger.info(f'Установлено соединение с сервером. Ответ сервера: {answer}')
#             print(f'Установлено соединение с сервером.')
#             print(f'Запущен клиент с парамертами: адрес сервера: {self.my_address}, '
#             f'порт: {self.my_port}, имя пользователя: {self.client_name}')
#             logger.info(
#             f'Запущен клиент с парамертами: адрес сервера: {self.my_address}, '
#             f'порт: {self.my_port}, имя пользователя: {self.client_name}')
#         except json.JSONDecodeError:
#             logger.error('Не удалось декодировать полученную Json строку.')
#             sys.exit(1)
#         except (ConnectionRefusedError, ConnectionError):
#             logger.critical(
#                 f'Не удалось подключиться к серверу {self.my_address}:{self.my_port}, '
#                 f'конечный компьютер отверг запрос на подключение.')
#             sys.exit(1)
#         else:
#         # Если соединение с сервером установлено корректно,
#         # запускаем клиенский процесс приёма сообщний
#             receiver = threading.Thread(target=self.message_from_server, args=(self.s, self.client_name))
#             receiver.daemon = True
#             receiver.start()
#         # затем запускаем отправку сообщений и взаимодействие с пользователем.
#             user_interface = threading.Thread(target=self.user_interactive, args=(self.s, self.client_name))
#             user_interface.daemon = True
#             user_interface.start()
#             logger.debug('Запущены процессы')
#             while True:
#                 time.sleep(1)
#                 if receiver.is_alive() and user_interface.is_alive():
#                     continue
#                 break


# @log
# def create_arg_parser():
#     parser = argparse.ArgumentParser()
#     parser.add_argument('addr', default='127.0.0.1', nargs='?')
#     parser.add_argument('port', default=7777, type=int, nargs='?')
#     parser.add_argument('-n', '--name', default=None, nargs='?')
#     return parser


# def main():
#     parser = create_arg_parser()
#     namespace = parser.parse_args(sys.argv[1:])
#     my_address = namespace.addr
#     my_port = namespace.port
#     client_name = namespace.name
#     my_client = Client(my_address, my_port, client_name)
#     my_client.main_client()
# if __name__ == '__main__':
#     main_client()