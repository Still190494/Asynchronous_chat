from socket import *

import sys
from utils import get_msg, send_msg, msg_to_server


def main():
    my_address = sys.argv[1]
    my_port = int(sys.argv[2])
    s = socket(AF_INET, SOCK_STREAM) # Создать сокет TCP
    s.connect((my_address, my_port)) # Соединиться с сервером
    msg_to_s = msg_to_server()
    send_msg(s, msg_to_s)
    answer = get_msg(s)
    print('Сообщение от сервера: ', answer)
    s.close()


if __name__ == '__main__':
    main()