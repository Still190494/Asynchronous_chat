# Программа сервера для получения приветствия от клиента и отправки ответа
import argparse
from socket import *
import sys
from utils import get_msg, send_msg, msg_to_client, msg_to_server
from logs.decor_log import log
import json
import logging
import logs.server_log_config
import select


sys.setrecursionlimit(10000)
logger = logging.getLogger('server')

@log
def process_client_message(message, messages_list, client):
    logger.debug(f'Разбор сообщения от клиента : {message}')
    response_msg = msg_to_server()
    # response_msg = msg_to_client()
    if 'action' in message and message['action'] == 'authenticate':
        send_msg(client, response_msg)
        return
    elif 'msg_text' in message:
        messages_list.append((message['user'], message['msg_text']))
        return
    
@log
def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=7777, type=int, nargs='?')
    parser.add_argument('-a', default='127.0.0.1', nargs='?')
    return parser



def main_server():
    parser = create_arg_parser()
    namespace = parser.parse_args(sys.argv[1:])
    my_address = namespace.a
    my_port = namespace.p
    clients = []
    messages = []
    try:
        if my_port < 1024 or my_port > 65535:
            raise ValueError
    except IndexError:
        logger.critical(f'Не верно указан порт сервера')
        sys.exit(1)
    except ValueError:
        logger.critical(f'Порт не может быть меньше "1024" или больше "65535"')
        sys.exit(1)
    try:
        if '-a' in sys.argv:
            my_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            my_address = '127.0.0.1'
    except IndexError:
        logger.critical(f'Не верно указан адресс сервера')
        sys.exit(1)
    s = socket(AF_INET, SOCK_STREAM) # Создает сокет TCP
    s.bind((my_address, my_port))
    s.listen(5) # Переходит в режим ожидания запросов;
                # Одновременно обслуживает не более
                # 5 запросов.
    while True:
        try:
            client, addr = s.accept()
        except OSError:
            pass
        else:
            logger.info(f'Установлено соедение с {addr}')
            print("Получен запрос на соединение от %s" % str(addr))
            clients.append(client)
        wait = 5
        r_list = []
        w_list = []
        err_list = []
        try:
            if clients:
                r_list, w_list, err_list = select.select(clients, clients, [], wait)
        except OSError:
            pass
        if r_list:
            for client_with_message in r_list:
                try:
                    process_client_message(get_msg(client_with_message),
                                           messages, client_with_message)
                except:
                    logger.info(f'Клиент {client_with_message.getpeername()} '
                                f'отключился от сервера.')
                    clients.remove(client_with_message)
        if messages and w_list:
            message = msg_to_client()
            del messages[0]
            for waiting_client in w_list:
                try:
                    send_msg(waiting_client, message)
                except:
                    logger.info(f'Клиент {waiting_client.getpeername()} отключился от сервера.')
                    clients.remove(waiting_client)
        # try:
        #     answer = get_msg(client)
        #     logger.info(f'Сообщение клиента {answer}')
        #     response_msg = msg_to_client()
        #     send_msg(client, response_msg)
        #     client.close()
        # except (ValueError, json.JSONDecodeError):
        #     logger.critical(f'Сообщение в неправильном формате')
        #     client.close()


if __name__ == '__main__':
    main_server()