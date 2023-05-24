# Программа сервера для получения приветствия от клиента и отправки ответа
import argparse
from socket import *
import sys
from utils import get_msg, send_msg, msg_to_client
from logs.decor_log import log
import json
import logging
import logs.server_log_config
import select


sys.setrecursionlimit(10000)
logger = logging.getLogger('server')


# @log
# def process_client_message(message, messages_list, client, clients, names):
#     """
#     Обработчик сообщений от клиентов, принимает словарь - сообщение от клиента,
#     проверяет корректность, отправляет словарь-ответ в случае необходимости.
#     :param message:
#     :param messages_list:
#     :param client:
#     :param clients:
#     :param names:
#     :return:
#     """
#     logger.debug(f'Разбор сообщения от клиента : {message}')
#     # Если это сообщение о присутствии, принимаем и отвечаем
#     if "action" in message and message["action"] == "presence" and \
#             "time" in message and "user" in message:
#         # Если такой пользователь ещё не зарегистрирован,
#         # регистрируем, иначе отправляем ответ и завершаем соединение.
#         if message["user"] not in names.keys():
#             names[message["user"]] = client
#             resp_ok = msg_to_client()
#             send_msg(client, resp_ok)
#         else:
#             response = {"response": 400,
#                     "error": None
#                     }
#             response["error"] = 'Имя пользователя уже занято.'
#             send_msg(client, response)
#             clients.remove(client)
#             client.close()
#         return   
#     # Если это сообщение, то добавляем его в очередь сообщений.
#     # Ответ не требуется.
#     elif "action" in message and message["action"] == 'message' and \
#             "to_user" in message and "time" in message \
#             and "from" in message and "msg_text" in message:
#         messages_list.append(message)
#         return
#     # Если клиент выходит
#     elif "action" in message and message["action"] == "exit" and "user" in message:
#         clients.remove(names[message["user"]])
#         names[message["user"]].close()
#         del names[message["user"]]
#         return
#     # Иначе отдаём Bad request
#     else:
#         response = {"response": 400,
#                     "error": None
#                     }
#         response["error"] = 'Запрос некорректен.'
#         send_msg(client, response)
#         return
    
@log
def create_arg_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', default=7777, type=int, nargs='?')
    parser.add_argument('-a', default='127.0.0.1', nargs='?')
    return parser


# @log
# def process_message(message, names, listen_socks):
#     """
#     Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение,
#     список зарегистрированых пользователей и слушающие сокеты. Ничего не возвращает.
#     :param message:
#     :param names:
#     :param listen_socks:
#     :return:
#     """
#     if message["to_user"] in names and names[message["to_user"]] in listen_socks:
#         send_msg(names[message["to_user"]], message)
#         logger.info(f'Отправлено сообщение пользователю {message["to_user"]} '
#                     f'от пользователя {message["from"]}.')
#     elif message["to_user"] in names and names[message["to_user"]] not in listen_socks:
#         raise ConnectionError
#     else:
#         logger.error(
#             f'Пользователь {message["to_user"]} не зарегистрирован на сервере, '
#             f'отправка сообщения невозможна.')

class Server():
    def __init__(self, my_address, my_port):
        self.my_address = my_address
        self.my_port = my_port
        self.clients = []
        self.messages = []
        self.names = dict()   

    def init_socket(self):
        try:
            if self.my_port < 1024 or self.my_port > 65535:
                raise ValueError
        except IndexError:
            logger.critical(f'Не верно указан порт сервера')
            sys.exit(1)
        except ValueError:
            logger.critical(f'Порт не может быть меньше "1024" или больше "65535"')
            sys.exit(1)
        try:
            if '-a' in sys.argv:
                self.my_address = sys.argv[sys.argv.index('-a') + 1]
            else:
                self.my_address = '127.0.0.1'
        except IndexError:
            logger.critical(f'Не верно указан адресс сервера')
            sys.exit(1)
        self.s = socket(AF_INET, SOCK_STREAM) # Создает сокет TCP
        self.s.bind((self.my_address, self.my_port))
        self.s.settimeout(0.5)
        self.s.listen(5) # Переходит в режим ожидания запросов;
                    # Одновременно обслуживает не более
                    # 5 запросов.


    @log
    def process_message(self, message, names, listen_socks):
        """
        Функция адресной отправки сообщения определённому клиенту. Принимает словарь сообщение,
        список зарегистрированых пользователей и слушающие сокеты. Ничего не возвращает.
        :param message:
        :param names:
        :param listen_socks:
        :return:
        """
        if message["to_user"] in self.names and self.names[message["to_user"]] in listen_socks:
            send_msg(self.names[message["to_user"]], message)
            logger.info(f'Отправлено сообщение пользователю {message["to_user"]} '
                        f'от пользователя {message["from"]}.')
        elif message["to_user"] in self.names and self.names[message["to_user"]] not in listen_socks:
            raise ConnectionError
        else:
            logger.error(
                f'Пользователь {message["to_user"]} не зарегистрирован на сервере, '
                f'отправка сообщения невозможна.')


    @log
    def process_client_message(self, message, messages_list, client, clients, names):
        """
        Обработчик сообщений от клиентов, принимает словарь - сообщение от клиента,
        проверяет корректность, отправляет словарь-ответ в случае необходимости.
        """
        logger.debug(f'Разбор сообщения от клиента : {message}')
        # Если это сообщение о присутствии, принимаем и отвечаем
        if "action" in message and message["action"] == "presence" and \
                "time" in message and "user" in message:
            # Если такой пользователь ещё не зарегистрирован,
            # регистрируем, иначе отправляем ответ и завершаем соединение.
            if message["user"] not in self.names.keys():
                self.names[message["user"]] = client
                resp_ok = msg_to_client()
                send_msg(client, resp_ok)
            else:
                response = {"response": 400,
                        "error": None
                        }
                response["error"] = 'Имя пользователя уже занято.'
                send_msg(client, response)
                self.clients.remove(client)
                client.close()
            return   
        # Если это сообщение, то добавляем его в очередь сообщений.
        # Ответ не требуется.
        elif "action" in message and message["action"] == 'message' and \
                "to_user" in message and "time" in message \
                and "from" in message and "msg_text" in message:
            self.messages_list.append(message)
            return
        # Если клиент выходит
        elif "action" in message and message["action"] == "exit" and "user" in message:
            self.clients.remove(names[message["user"]])
            self.names[message["user"]].close()
            del self.names[message["user"]]
            return
        # Иначе отдаём Bad request
        else:
            response = {"response": 400,
                        "error": None
                        }
            response["error"] = 'Запрос некорректен.'
            send_msg(client, response)
            return
        

    def main_server(self):
        self.init_socket()


        while True:
            try:
                self.client, self.addr = self.s.accept()
            except OSError:
                pass
            else:
                logger.info(f'Установлено соедение с {self.addr}')
                print("Получен запрос на соединение от %s" % str(self.addr))
                self.clients.append(self.client)

            recv_list = []
            send_list = []
            err_list = []
            try:
                if self.clients:
                    recv_list, send_list, err_list = select.select(self.clients, self.clients, [], 0)
            except OSError:
                pass
            if recv_list:
                for client_with_message in recv_list:
                    try:
                        self.process_client_message(get_msg(client_with_message),
                                            self.messages, client_with_message, self.clients, self.names)
                    except:
                        logger.info(f'Клиент {client_with_message.getpeername()} '
                                    f'отключился от сервера.')
                        self.clients.remove(client_with_message)
            for i in self.messages:
                try:
                    self.process_message(i, self.names, send_list)
                except Exception:
                    logger.info(f'Связь с клиентом с именем {i["to_user"]} была потеряна')
                    self.clients.remove(self.names[i["to_user"]])
                    del self.names[i["to_user"]]
            self.messages.clear()
    print('Запущен сервер')






# def main_server():
#     parser = create_arg_parser()
#     namespace = parser.parse_args(sys.argv[1:])
#     my_address = namespace.a
#     my_port = namespace.p
#     clients = []
#     messages = []
#     names = dict()
#     try:
#         if my_port < 1024 or my_port > 65535:
#             raise ValueError
#     except IndexError:
#         logger.critical(f'Не верно указан порт сервера')
#         sys.exit(1)
#     except ValueError:
#         logger.critical(f'Порт не может быть меньше "1024" или больше "65535"')
#         sys.exit(1)
#     try:
#         if '-a' in sys.argv:
#             my_address = sys.argv[sys.argv.index('-a') + 1]
#         else:
#             my_address = '127.0.0.1'
#     except IndexError:
#         logger.critical(f'Не верно указан адресс сервера')
#         sys.exit(1)
#     s = socket(AF_INET, SOCK_STREAM) # Создает сокет TCP
#     s.bind((my_address, my_port))
#     s.settimeout(0.5)
#     s.listen(5) # Переходит в режим ожидания запросов;
#                 # Одновременно обслуживает не более
#                 # 5 запросов.
#     while True:
#         try:
#             client, addr = s.accept()
#         except OSError:
#             pass
#         else:
#             logger.info(f'Установлено соедение с {addr}')
#             print("Получен запрос на соединение от %s" % str(addr))
#             clients.append(client)

#         recv_list = []
#         send_list = []
#         err_list = []
#         try:
#             if clients:
#                 recv_list, send_list, err_list = select.select(clients, clients, [], 0)
#         except OSError:
#             pass
#         if recv_list:
#             for client_with_message in recv_list:
#                 try:
#                     process_client_message(get_msg(client_with_message),
#                                            messages, client_with_message, clients, names)
#                 except:
#                     logger.info(f'Клиент {client_with_message.getpeername()} '
#                                 f'отключился от сервера.')
#                     clients.remove(client_with_message)
#         for i in messages:
#             try:
#                 process_message(i, names, send_list)
#             except Exception:
#                 logger.info(f'Связь с клиентом с именем {i["to_user"]} была потеряна')
#                 clients.remove(names[i["to_user"]])
#                 del names[i["to_user"]]
#         messages.clear()
# print('Запущен сервер')
def main():
    parser = create_arg_parser()
    namespace = parser.parse_args(sys.argv[1:])
    my_address = namespace.a
    my_port = namespace.p
    my_server = Server(my_address, my_port)
    my_server.main_server()



if __name__ == '__main__':
    main()