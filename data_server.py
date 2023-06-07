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
from server_gui import MainWindow, gui_create_model, HistoryWindow, create_stat_model, ConfigWindow
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import os.path


logger = logging.getLogger('server')
# Флаг что был подключён новый пользователь, нужен чтобы не мучать BD
# постоянными запросами на обновление
new_connection = False
conflag_lock = threading.Lock()

@log
def create_arg_parser(default_port, default_address):
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=default_port, type=int, nargs='?')
    parser.add_argument('-a', default=default_address, nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    my_address = namespace.a
    my_port = namespace.p
    return my_address, my_port

class Server(threading.Thread, metaclass=ServerVerifier):
    my_port = DescriptPort()
    def __init__(self, my_address, my_port, database):
        super().__init__()
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
        if message['to'] in self.names and self.names[message['to']] in listen_socks:
            send_msg(self.names[message['to']], message)
            logger.info(f'Отправлено сообщение пользователю {message["to"]} '
                        f'от пользователя {message["from"]}.')
        elif message['to'] in self.names and self.names[message['to']] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(
                f'Пользователь {message["to_user"]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')


    @log
    def process_client_message(self, message, client):
        global new_connection
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
            if message["user"]['account_name'] not in self.names.keys():
                self.names[message["user"]['account_name']] = client
                client_ip, client_port = client.getpeername()
                # resp_ok = msg_to_client()
                self.database.user_login(
                    message["user"]['account_name'], client_ip, client_port)
                resp_ok = {'response': 200}
                send_msg(client, resp_ok)
                with conflag_lock:
                    new_connection = True
            else:
                response = {"response": 400,
                            "error": None}
                response["error"] = 'Имя пользователя уже занято.'
                send_msg(client, response)
                self.clients.remove(client)
                client.close()
            return
        # Если это сообщение, то добавляем его в очередь сообщений.
        # Ответ не требуется.
        elif "action" in message and message["action"] == 'message' and 'to' in message and 'time' in message \
                and 'from' in message and 'mess_text' in message and self.names[message['from']] == client:
            self.messages.append(message)
            self.database.process_message(
                message['from'], message['to'])
            return
        # Если клиент выходит
        elif "action" in message and message["action"] == "exit" and "account_name" in message \
                and self.names[message["account_name"]] == client:
            self.database.user_logout(message["account_name"])
            self.clients.remove(self.names[message["account_name"]])
            self.names[message["account_name"]].close()
            del self.names[message["account_name"]]
            with conflag_lock:
                new_connection = True
            return

        # Если это запрос контакт-листа
        elif "action" in message and message["action"] == 'get_contacts' and "user" in message and \
                self.names[message["user"]] == client:
            response = {'response':202}
            response['data_list'] = self.database.get_contacts(message["user"])
            send_msg(client, response)

        # Если это добавление контакта
        elif "action" in message and message["action"] == 'add' and "account_name" and 'user' in message and \
                self.names[message["user"]] == client:
            self.database.add_contact(message["user"], message["account_name"])
            response = {'response':200}
            send_msg(client, response)

        # Если это удаление контакта
        elif "action" in message and message["action"] == 'remove' and "account_name" and 'user' in message \
                and self.names[message["user"]] == client:
            self.database.remove_contact(message["user"], message["account_name"])
            response = {'response':200}
            send_msg(client, response)

        # Если это запрос известных пользователей
        elif "action" in message and message["action"] == 'get_users' and "account_name" in message \
                and self.names[message["account_name"]] == client:
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
                    except (OSError):
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
                except (ConnectionAbortedError, ConnectionError, ConnectionResetError, ConnectionRefusedError):
                    logger.info(f'Связь с клиентом с именем {i["to"]} была потеряна')
                    self.clients.remove(self.names[i["to"]])
                    self.database.user_logout(i["to"])
                    del self.names[i["to"]]
            self.messages.clear()
    print('Запущен сервер')


def main():
    config = configparser.ConfigParser()
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config.read(f"{dir_path}/{'server.ini'}")
    # Загрузка параметров командной строки, если нет параметров, то задаём
    # значения по умоланию.
    my_address, my_port = create_arg_parser(
        config['SETTINGS']['Default_port'], config['SETTINGS']['Listen_Address'])
    # Инициализация базы данных
    database = ServerDB(
        os.path.join(
            config['SETTINGS']['Database_path'],
            config['SETTINGS']['Database_file']))
    # Создание экземпляра класса - сервера и его запуск:
    my_server = Server(my_address, my_port, database)
    my_server.daemon = True
    my_server.start()
    # my_server.run()

    # Создаём графическое окуружение для сервера:
    server_app = QApplication(sys.argv)
    main_window = MainWindow()

    # Инициализируем параметры в окна
    main_window.statusBar().showMessage('Server Working')
    main_window.active_clients_table.setModel(gui_create_model(database))
    main_window.active_clients_table.resizeColumnsToContents()
    main_window.active_clients_table.resizeRowsToContents()

    # Функция обновляющяя список подключённых, проверяет флаг подключения, и
    # если надо обновляет список
    def list_update():
        global new_connection
        if new_connection:
            main_window.active_clients_table.setModel(
                gui_create_model(database))
            main_window.active_clients_table.resizeColumnsToContents()
            main_window.active_clients_table.resizeRowsToContents()
            with conflag_lock:
                new_connection = False

    # Функция создающяя окно со статистикой клиентов
    def show_statistics():
        global stat_window
        stat_window = HistoryWindow()
        stat_window.history_table.setModel(create_stat_model(database))
        stat_window.history_table.resizeColumnsToContents()
        stat_window.history_table.resizeRowsToContents()
        stat_window.show()

    # Функция создающяя окно с настройками сервера.
    def server_config():
        global config_window
        # Создаём окно и заносим в него текущие параметры
        config_window = ConfigWindow()
        config_window.db_path.insert(config['SETTINGS']['Database_path'])
        config_window.db_file.insert(config['SETTINGS']['Database_file'])
        config_window.port.insert(config['SETTINGS']['Default_port'])
        config_window.ip.insert(config['SETTINGS']['Listen_Address'])
        config_window.save_btn.clicked.connect(save_server_config)

    # Функция сохранения настроек
    def save_server_config():
        global config_window
        message = QMessageBox()
        config['SETTINGS']['Database_path'] = config_window.db_path.text()
        config['SETTINGS']['Database_file'] = config_window.db_file.text()
        try:
            port = int(config_window.port.text())
        except ValueError:
            message.warning(config_window, 'Ошибка', 'Порт должен быть числом')
        else:
            config['SETTINGS']['Listen_Address'] = config_window.ip.text()
            if 1023 < port < 65536:
                config['SETTINGS']['Default_port'] = str(port)
                print(port)
                with open('server.ini', 'w') as conf:
                    config.write(conf)
                    message.information(
                        config_window, 'OK', 'Настройки успешно сохранены!')
            else:
                message.warning(
                    config_window,
                    'Ошибка',
                    'Порт должен быть от 1024 до 65536')

    # Таймер, обновляющий список клиентов 1 раз в секунду
    timer = QTimer()
    timer.timeout.connect(list_update)
    timer.start(1000)

    # Связываем кнопки с процедурами
    main_window.refresh_button.triggered.connect(list_update)
    main_window.show_history_button.triggered.connect(show_statistics)
    main_window.config_btn.triggered.connect(server_config)

    # Запускаем GUI
    server_app.exec_()

if __name__ == '__main__':
    main()