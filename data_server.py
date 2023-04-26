# Программа сервера для получения приветствия от клиента и отправки ответа
from socket import *
import time
import json
import sys


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
        client_js_msg = client.recv(1000000)
        client_msg_decode = client_js_msg.decode('utf-8')
        msg_client = json.loads(client_msg_decode)
        print("Сообщение клиента", msg_client)
        response_msg = {
            "response": 200,
        }
        js_response = json.dumps(response_msg)
        client.send(js_response.encode('utf-8'))
        client.close()


if __name__ == '__main__':
    main()