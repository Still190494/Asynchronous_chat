from socket import *
import json
import sys
from utils import get_msg, send_msg, msg_to_server


def main():
    try:
        my_address = sys.argv[1]
        my_port = int(sys.argv[2])
        if my_port < 1024 or my_port > 65535:
            raise ValueError
    except IndexError:
        my_address = '127.0.0.1'
        my_port = 7777
    except ValueError:
        print('Порт не может быть меньше "1024" или больше "65535"')
        sys.exit(1)
    s = socket(AF_INET, SOCK_STREAM) # Создать сокет TCP
    s.connect((my_address, my_port)) # Соединиться с сервером
    msg_to_s = msg_to_server()
    send_msg(s, msg_to_s)
    try:
        answer = get_msg(s)
        print('Сообщение от сервера: ', answer)
    except (ValueError, json.JSONDecodeError):
        print('Сообщение в неправильном формате')
    s.close()


if __name__ == '__main__':
    main()