Сервер
=================================================

Серверный модуль мессенджера. Обрабатывает словари - сообщения, хранит публичные ключи клиентов.

Использование

Модуль поддерживает аргументы командной строки:

1. -p - Порт на котором принимаются соединения
2. -a - Адрес с которого принимаются соединения.
3. --no_gui Запуск только основных функций, без графической оболочки.

* В данном режиме поддерживается только 1 команда: exit - завершение работы.

Примеры использования:

``python data_server.py -p 7777 -a localhost``

data_server.py
~~~~~~~~~~~~~~

Запускает парсер аргументов.

data_server. **create_arg_parser** ()
    Функция - парсер командной строки

Запускает основную программу.

core.py
~~~~~~~~~~~

.. autoclass:: Asynchronous_chat.server.core.MessageProcessor
    :members:

server_db.py
~~~~~~~~~~~~

.. autoclass:: Asynchronous_chat.server.server_db.ServerDB
    :members:

main_window.py
~~~~~~~~~~~~~~

.. autoclass:: Asynchronous_chat.server.main_window.MainWindow
    :members:

add_user.py
~~~~~~~~~~~

.. autoclass:: Asynchronous_chat.server.add_user.RegisterUser
    :members:

remove_user.py
~~~~~~~~~~~~~~

.. autoclass:: Asynchronous_chat.server.remove_user.DelUserDialog
    :members:

config_window.py
~~~~~~~~~~~~~~~~

.. autoclass:: Asynchronous_chat.server.config_window.ConfigWindow
    :members:

stat_window.py
~~~~~~~~~~~~~~

.. autoclass:: Asynchronous_chat.server.stat_window.StatWindow
    :members: