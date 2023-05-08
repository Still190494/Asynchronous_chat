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
    msg = {
    "action": "authenticate",
    "time": time.time(),
    "user": {
        "account_name": "admin",
        "password": "adminpass"
        }
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
