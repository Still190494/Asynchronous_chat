import inspect
import json
import time
import sys
import logging
import traceback
from logs.decor_log import log
from errors import IncorrectDataRecivedError, NonDictInputError
sys.setrecursionlimit(10000)


# """Сообщение для сервера"""
# @log
# def msg_to_server():
#     text_msg = input('Напишите сообщение: ')
#     to_user = input('Введите пользователя: ')
#     msg = {
#     "action": "authenticate",
#     "time": time.time(),
#     "user": "admin",
#     "to_users": to_user,
#     "msg_text": text_msg
#     }
#     return msg


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
    encoded_response = client.recv(1024)
    if isinstance(encoded_response, bytes):
        json_response = encoded_response.decode('utf-8')
        response = json.loads(json_response)
        if isinstance(response, dict):
            return response
        else:
            raise IncorrectDataRecivedError
    else:
        raise IncorrectDataRecivedError


'''Энкодим и отправляем сообщение'''
@log
def send_msg(s, msg):
    if not isinstance(msg, dict):
        raise NonDictInputError
    js_message = json.dumps(msg)
    encoded_message = js_message.encode('utf-8')
    s.send(encoded_message)

'''выход'''
@log
def create_exit_message(account_name):
    return {
        "action": "exit",
        "time": time.time(),
        "user": account_name
    }
