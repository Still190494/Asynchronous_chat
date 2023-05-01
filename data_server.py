# Программа сервера для получения приветствия от клиента и отправки ответа
from socket import *
import sys
from utils import get_msg, send_msg, msg_to_client


def main():
    my_port = int(sys.argv[sys.argv.index('-p') + 1])
    my_address = sys.argv[sys.argv.index('-a') + 1]
    s = socket(AF_INET, SOCK_STREAM) # Создает сокет TCP
    s.bind((my_address, my_port))
    s.listen(5) # Переходит в режим ожидания запросов;
    # Одновременно обслуживает не более
    # 5 запросов.
    while True:
        client, addr = s.accept()
        answer = get_msg(client)
        print("Сообщение клиента", answer)
        response_msg = msg_to_client()
        send_msg(client, response_msg)
        client.close()


if __name__ == '__main__':
    main()