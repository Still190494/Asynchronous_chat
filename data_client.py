import sys
import os
import logging
import argparse

from PyQt5.QtWidgets import QApplication, QMessageBox
from Cryptodome.PublicKey import RSA

from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from logs.decor_log import log
from client.transport import ClientTransport
from client.client_db import ClientDB
from Asynchronous_chat.utils.errors import ServerError

logger = logging.getLogger('client')


@log
def create_arg_parser():
    """Функция - парсер командной строки"""
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default='127.0.0.1', nargs='?')
    parser.add_argument('port', default=7777, type=int, nargs='?')
    parser.add_argument('-n', '--name', default=None, nargs='?')
    parser.add_argument('-p', '--password', default='', nargs='?')
    namespace = parser.parse_args(sys.argv[1:])
    my_address = namespace.addr
    my_port = namespace.port
    client_name = namespace.name
    client_passwd = namespace.password
    # проверим подходящий номер порта
    if not 1023 < my_port < 65536:
        logger.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {my_port}.'
            f' Допустимы адреса с 1024 до 65535. Клиент завершается.')
        exit(1)
    return my_address, my_port, client_name, client_passwd


if __name__ == '__main__':
    my_address, my_port, client_name, client_passwd = create_arg_parser()
    client_app = QApplication(sys.argv)
    start_dialog = UserNameDialog()
    if not client_name:
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект, иначе выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            client_passwd = start_dialog.client_passwd.text()
            logger.debug(f'Using USERNAME = {client_name}, PASSWD = {client_passwd}.')
        else:
            exit(0)
            # Записываем логи
            logger.info(
                f'Запущен клиент с парамертами: адрес сервера: {my_address} , порт: {my_port}, имя пользователя: {client_name}')
    # Загружаем ключи с файла, если же файла нет, то генерируем новую пару.
    dir_path = os.path.dirname(os.path.realpath(__file__))
    key_file = os.path.join(dir_path, f'{client_name}.key')
    if not os.path.exists(key_file):
        keys = RSA.generate(2048, os.urandom)
        with open(key_file, 'wb') as key:
            key.write(keys.export_key())
    else:
        with open(key_file, 'rb') as key:
            keys = RSA.import_key(key.read())
    database = ClientDB(client_name)
    try:
        transport = ClientTransport(my_port, my_address, database, client_name, client_passwd, keys)
        logger.debug("Transport ready.")
    except ServerError as error:
        message = QMessageBox()
        message.critical(start_dialog, 'Ошибка сервера', error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()
    del start_dialog
    # Создаём GUI
    main_window = ClientMainWindow(database, transport, keys)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат - {client_name}')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()
