import sys

from client.main_window import ClientMainWindow
from client.start_dialog import UserNameDialog
from logs.decor_log import log
import logging
import argparse
from client.transport import ClientTransport
from client.client_db import ClientDB
from errors import ServerError
from PyQt5.QtWidgets import QApplication


logger = logging.getLogger('client')


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

    # проверим подходящий номер порта
    if not 1023 < my_port < 65536:
        logger.critical(
            f'Попытка запуска клиента с неподходящим номером порта: {my_port}.'
            f' Допустимы адреса с 1024 до 65535. Клиент завершается.')
        exit(1)
    return my_address, my_port, client_name


if __name__ == '__main__':
    my_address, my_port, client_name = create_arg_parser()
    client_app = QApplication(sys.argv)

    if not client_name:
        start_dialog = UserNameDialog()
        client_app.exec_()
        # Если пользователь ввёл имя и нажал ОК, то сохраняем ведённое и удаляем объект, инааче выходим
        if start_dialog.ok_pressed:
            client_name = start_dialog.client_name.text()
            del start_dialog
        else:
            exit(0)

    database = ClientDB(client_name)
    try:
        transport = ClientTransport(my_port, my_address, database, client_name)
    except ServerError as error:
        print(error.text)
        exit(1)
    transport.setDaemon(True)
    transport.start()

    # Создаём GUI
    main_window = ClientMainWindow(database, transport)
    main_window.make_connection(transport)
    main_window.setWindowTitle(f'Чат - {client_name}')
    client_app.exec_()

    # Раз графическая оболочка закрылась, закрываем транспорт
    transport.transport_shutdown()
    transport.join()



