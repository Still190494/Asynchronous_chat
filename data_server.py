# Программа сервера для получения приветствия от клиента и отправки ответа
import argparse
import configparser
import socket
import sys
import os
import threading
from utils import get_msg, send_msg, msg_to_client
from logs.decor_log import log
from descriptors import DescriptPort
from server_db import ServerDB
import json
import logging
import logs.server_log_config
import select
from metaclasses import ServerVerifier
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QTimer
# from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import os.path

sys.setrecursionlimit(10000)
logger = logging.getLogger('server')

   
@log
def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=7777, type=int, nargs='?')
    parser.add_argument('-a', default='127.0.0.1', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    my_address = namespace.a
    my_port = namespace.p
    return my_address, my_port

class Server(metaclass=ServerVerifier):
    my_port = DescriptPort()
    def __init__(self, my_address, my_port, database):
        self.my_address = my_address
        self.my_port = my_port
        self.clients = []
        self.messages = []
        self.names = dict()
        self.database = database   


    def init_socket(self):
        try:
            if '-a' in sys.argv:
                self.my_address = sys.argv[sys.argv.index('-a') + 1]
            else:
                self.my_address = '127.0.0.1'
        except IndexError:
            logger.critical(f'Не верно указан адресс сервера')
            sys.exit(1)
        my_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        my_server.bind((self.my_address, self.my_port))
        my_server.settimeout(0.5)

        # Начинаем слушать сокет.
        self.my_server = my_server
        self.my_server.listen()

    @log
    def process_message(self, message, listen_socks):
        """
        Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение,
        список зарегистрированых пользователей и слушающие сокеты. Ничего не возвращает.
        """
        if message["to_user"] in self.names and self.names[message["to_user"]] in listen_socks:
            send_msg(self.names[message["to_user"]], message)
            logger.info(f'Отправлено сообщение пользователю {message["to_user"]} '
                        f'от пользователя {message["from"]}.')
        elif message["to_user"] in self.names and self.names[message["to_user"]] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(
                f'Пользователь {message["to_user"]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')


    @log
    def process_client_message(self, message, client,):
        """
        Обработчик сообщений от клиентов, принимает словарь - сообщение от клиента,
        проверяет корректность, отправляет словарь-ответ в случае необходимости.
        """
        logger.debug(f'Разбор сообщения от клиента : {message}')
        # Если это сообщение о присутствии, принимаем и отвечаем
        if "action" in message and message["action"] == "presence" and \
                "time" in message and "user" in message:
            # Если такой пользователь ещё не зарегистрирован,
            # регистрируем, иначе отправляем ответ и завершаем соединение.
            if message["user"] not in self.names.keys():
                self.names[message["user"]] = client
                client_ip, client_port = client.getpeername()
                resp_ok = msg_to_client()
                self.database.user_login(
                    message["user"], client_ip, client_port)
                send_msg(client, resp_ok)
            else:
                response = {"response": 400,
                        "error": None
                        }
                response["error"] = 'Имя пользователя уже занято.'
                send_msg(client, response)
                self.clients.remove(client)
                client.close()
            return   
        # Если это сообщение, то добавляем его в очередь сообщений.
        # Ответ не требуется.
        elif "action" in message and message["action"] == 'message' and \
                "to_user" in message and "time" in message \
                and "from" in message and "msg_text" in message:
            self.messages.append(message)
            self.database.process_message(
                message['from'], message['to'])
            return
        # Если клиент выходит
        elif "action" in message and message["action"] == "exit" and "user" in message:
            self.database.user_logout(message["user"])
            self.clients.remove(self.names[message["user"]])
            self.names[message["user"]].close()
            del self.names[message["user"]]
            return
        
        # Если это запрос контакт-листа
        elif "action" in message and message["action"] == 'get_contacts' and "user" in message and \
                self.names[message["user"]] == client:
            response = {'response':202}
            response['data_list'] = self.database.get_contacts(message["user"])
            send_msg(client, response)

        # Если это добавление контакта
        elif "action" in message and message["action"] == 'add_contacts' and "user" in message and \
                self.names[message["user"]] == client:
            self.database.add_contact(message["user"], message["user"])
            response = {'response':200}
            send_msg(client, response)

        # Если это удаление контакта
        elif "action" in message and message["action"] == 'remove_contacts' and "user" in message \
                and self.names[message["user"]] == client:
            self.database.remove_contact(message["user"], message["user"])
            response = {'response':200}
            send_msg(client, response)

        # Если это запрос известных пользователей
        elif "action" in message and message["action"] == 'get_user' and "user" in message \
                and self.names[message["user"]] == client:
            response = {'response':202}
            response['data_list'] = [user[0]
                                   for user in self.database.users_list()]
            send_msg(client, response)





        # Иначе отдаём Bad request
        else:
            response = {"response": 400,
                        "error": None
                        }
            response["error"] = 'Запрос некорректен.'
            send_msg(client, response)
            return
        

    def run(self):
        self.init_socket()
        while True:
            try:
                client, addr = self.my_server.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соедение с {addr}')
                print("Получен запрос на соединение от %s" % str(addr))
                self.clients.append(client)
            recv_list = []
            send_list = []
            err_list = []
            try:
                if self.clients:
                    recv_list, send_list, err_list = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass
            if recv_list:
                for client_with_message in recv_list:
                    try:
                        self.process_client_message(get_msg(client_with_message), client_with_message)
                    except:
                        logger.info(f'Клиент {client_with_message.getpeername()} '
                                    f'отключился от сервера.')
                        for name in self.names:
                            if self.names[name] == client_with_message:
                                self.database.user_logout(name)
                                del self.names[name]
                                break
                        self.clients.remove(client_with_message)
            for i in self.messages:
                try:
                    self.process_message(i, send_list)
                except Exception:
                    logger.info(f'Связь с клиентом с именем {i["to_user"]} была потеряна')
                    self.clients.remove(self.names[i["to_user"]])
                    self.database.user_logout(i["to_user"])
                    del self.names[i["to_user"]]
            self.messages.clear()
    print('Запущен сервер')


def main():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    # Загрузка параметров командной строки, если нет параметров, то задаём
    # значения по умоланию.
    my_address, my_port = create_arg_parser()
    # Инициализация базы данных
    database = ServerDB(
        os.path.join(
            config['SETTINGS']['database_path'],
            config['SETTINGS']['database_file']))
    # Создание экземпляра класса - сервера и его запуск:
    my_server = Server(my_address, my_port, database)
    my_server.daemon = True
    my_server.start()
    # my_server.run()


if __name__ == '__main__':
    main()