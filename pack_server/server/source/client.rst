Клиент
=================================================

Клиентское приложение.

Поддерживает аргументы командной строки:

``python data_client.py {имя сервера} {порт} -n или --name {имя пользователя} -p или -password {пароль}``

1. {имя сервера} - адрес сервера сообщений.
2. {порт} - порт по которому принимаются подключения
3. -n или --name - имя пользователя с которым произойдёт вход в систему.
4. -p или --password - пароль пользователя.

Все опции командной строки являются необязательными, но имя пользователя и пароль необходимо использовать в паре.

data_client.py
~~~~~~~~~~~~~~

Запускает парсер аргументов.

data_client. **create_arg_parser** ()
    Функция - парсер командной строки

Запускает основную программу.

Пример использования:

``data_client.py localhost 7777 -n artem -p 123``


client_db.py
~~~~~~~~~~~~~~

.. autoclass:: Asynchronous_chat.client.client_db.ClientDB
    :members:
	
transport.py
~~~~~~~~~~~~~~

.. autoclass:: Asynchronous_chat.client.transport.ClientTransport
    :members:

main_window.py
~~~~~~~~~~~~~~

.. autoclass:: Asynchronous_chat.client.main_window.ClientMainWindow
    :members:

start_dialog.py
~~~~~~~~~~~~~~~

.. autoclass:: Asynchronous_chat.client.start_dialog.UserNameDialog
    :members:


add_contact.py
~~~~~~~~~~~~~~

.. autoclass:: Asynchronous_chat.client.add_contact.AddContactDialog
    :members:
	
	
del_contact.py
~~~~~~~~~~~~~~

.. autoclass:: Asynchronous_chat.client.del_contact.DelContactDialog
    :members: