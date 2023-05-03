# Программа сервера для получения приветствия от клиента и отправки ответа
from socket import *
import sys
from utils import get_msg, send_msg, msg_to_client
import json

def main():
    try:
        if '-p' in sys.argv:
            my_port = int(sys.argv[sys.argv.index('-p') + 1])
        else:
            my_port = 7777
        if my_port < 1024 or my_port > 65535:
            raise ValueError
    except IndexError:
        print('Не верно указан порт сервера')
        sys.exit(1)
    except ValueError:
        print('Порт не может быть меньше "1024" или больше "65535"')
        sys.exit(1)
    try:
        if '-a' in sys.argv:
            my_address = sys.argv[sys.argv.index('-a') + 1]
        else:
            my_address = '127.0.0.1'
    except IndexError:
        print('Не верно указан адресс сервера')
        sys.exit(1)
    s = socket(AF_INET, SOCK_STREAM) # Создает сокет TCP
    s.bind((my_address, my_port))
    s.listen(5) # Переходит в режим ожидания запросов;
                # Одновременно обслуживает не более
                # 5 запросов.
    while True:
        client, addr = s.accept()
        try:
            answer = get_msg(client)
            print("Сообщение клиента", answer)
            response_msg = msg_to_client()
            send_msg(client, response_msg)
            client.close()
        except (ValueError, json.JSONDecodeError):
            print('Сообщение в неправильном формате')
            client.close()


if __name__ == '__main__':
    main()