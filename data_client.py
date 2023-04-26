from socket import *
import time
import json
import sys

def main():
    my_address = sys.argv[1]
    my_port = int(sys.argv[2])
    s = socket(AF_INET, SOCK_STREAM) # Создать сокет TCP
    s.connect((my_address, my_port)) # Соединиться с сервером
    msg = {
        "action": "authenticate",
        "time": time.time(),
        "user": {
            "account_name": "admin",
            "password": "adminpass"
            }
        }
    js_msg = json.dumps(msg)
    s.send(js_msg.encode('utf-8'))
    server_msg_js = s.recv(1024)
    server_msg_decode = server_msg_js.decode('utf-8')
    server_msg = json.loads(server_msg_decode)
    print('Сообщение от сервера: ', server_msg)
    s.close()


if __name__ == '__main__':
    main()