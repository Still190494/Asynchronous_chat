import inspect
import json
import time
import sys
import logging
import traceback
from logs.decor_log import log


@log
def msg_to_client():
    """Ответ клиенту"""
    response_msg = {
        "response": 200,
    }
    return response_msg


@log
def get_msg(client):
    """Функция получения и декодирования сообщений"""
    encoded_response = client.recv(1024)
    json_response = encoded_response.decode('utf-8')
    response = json.loads(json_response)
    if isinstance(response, dict):
        return response
    else:
        raise TypeError


@log
def send_msg(s, msg):
    """Функция энкодинга и отправки сообщений"""
    js_message = json.dumps(msg)
    encoded_message = js_message.encode('utf-8')
    s.send(encoded_message)


@log
def create_exit_message(account_name):
    """Функция возвращающая сообщение о выходе"""
    return {
        "action": "exit",
        "time": time.time(),
        "user": account_name
    }
