import inspect
import json
import time
import sys
import logging
import traceback
from logs.decor_log import log

sys.setrecursionlimit(10000)


"""Сообщение для сервера"""
@log
def msg_to_server():
    text_msg = input('Напишите сообщение: ')
    to_user = input('Введите пользователя: ')
    msg = {
    "action": "authenticate",
    "time": time.time(),
    "user": "admin",
    "to_users": to_user,
    "msg_text": text_msg
    }
    return msg


"""Сообщение для клиента"""
@log
def msg_to_client():
    response_msg = {
        "response": 200,
    }
    return response_msg




"""Получаем и декодим сообщение"""
@log
def get_msg(client):
    msg_js = client.recv(1024)
    msg_decode = msg_js.decode('utf-8')
    msg = json.loads(msg_decode)
    return msg


'''Энкодим и отправляем сообщение'''
@log
def send_msg(s, msg):
    js_msg = json.dumps(msg)
    s.send(js_msg.encode('utf-8'))

'''выход'''
@log
def create_exit_message(account_name):
    return {
        "action": "exit",
        "time": time.time(),
        "user": account_name
    }
