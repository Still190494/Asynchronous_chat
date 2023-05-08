from socket import *
import json
import sys
from utils import get_msg, send_msg, msg_to_server
from logs.decor_log import log
import logging
import logs.client_log_config
import argparse

sys.setrecursionlimit(10000)
logger = logging.getLogger('client')


@log
def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('addr', default='127.0.0.1', nargs='?')
    parser.add_argument('port', default=7777, type=int, nargs='?')
    return parser



def main_client():
    parser = create_arg_parser()
    namespace = parser.parse_args(sys.argv[1:])
    try:
        my_address = namespace.addr
        my_port = namespace.port
        if my_port < 1024 or my_port > 65535:
            raise ValueError
    except IndexError:
        my_address = '127.0.0.1'
        my_port = 7777
    except ValueError:
        logger.critical(f'Указан не верный порт!!! Порт не может быть меньше "1024" или больше "65535"')
        sys.exit(1)
    s = socket(AF_INET, SOCK_STREAM) # Создать сокет TCP
    s.connect((my_address, my_port)) # Соединиться с сервером
    msg_to_s = msg_to_server()
    send_msg(s, msg_to_s)
    try:
        answer = get_msg(s)
        logger.info(f'Сообщение от сервера: {answer}')
    except (ValueError, json.JSONDecodeError):
        logger.critical(f'Сообщение в неправильном формате')
    s.close()


if __name__ == '__main__':
    main_client()