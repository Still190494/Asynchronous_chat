import datetime
from sqlalchemy import DateTime, create_engine, Table, Column, Integer, String, MetaData, ForeignKey, Text
from sqlalchemy.orm import registry, sessionmaker

class ServerDB:
    # Класс - отображение таблицы всех пользователей
    class Client_table:
        def __init__(self, username, passwd_hash):
            self.id = None
            self.pubkey = None
            self.name = username
            self.passwd_hash = passwd_hash
            self.last_login = datetime.datetime.now()


    # Класс отображение таблицы истории действий
    class UsersHistory:
        def __init__(self, user):
            self.id = None
            self.user = user
            self.sent = 0
            self.accepted = 0

    # Класс - отображение таблицы контактов пользователей
    class Contact_list:
        def __init__(self, user, contact):
            self.id = None
            self.user = user
            self.contact = contact

    # Класс - отображение таблицы активных пользователей:
    class ActiveUsers:
        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    # Класс - отображение таблицы истории входов
    class LoginHistory:
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port


    def __init__(self, path) -> object:
        self.engine = create_engine(f'sqlite:///{path}', echo=False, pool_recycle=7200, connect_args={'check_same_thread': False})
        self.metadata = MetaData()
        """Таблица всех пользователей"""
        client_table = Table('users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime),
                            Column('passwd_hash', String),
                            Column('pubkey', Text)
                            )

        """Создаём таблицу истории пользователей"""
        users_history_table = Table('history', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('user', ForeignKey('users.id')),
                                    Column('sent', Integer),
                                    Column('accepted', Integer)
                                    )

        """Список контактов"""
        contact_list_table = Table('contact_list', self.metadata,
                                Column('id', Integer, primary_key=True),
                                Column('user', ForeignKey('users.id')),
                                Column('contact', ForeignKey('users.id')),
                                )

        """Таблица активных пользователей"""
        active_users_table = Table('active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('users.id'), unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime)
                                   )
        
        """Создаём таблицу истории входов"""
        user_login_history = Table('login_history', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('name', ForeignKey('users.id')),
                                   Column('date_time', DateTime),
                                   Column('ip', String),
                                   Column('port', String)
                                   )
        
        self.metadata.create_all(self.engine)
        mapper_registry = registry()
        mapper_registry.map_imperatively(self.Client_table, client_table)
        mapper_registry.map_imperatively(self.UsersHistory, users_history_table)
        mapper_registry.map_imperatively(self.Contact_list, contact_list_table)
        mapper_registry.map_imperatively(self.ActiveUsers, active_users_table)
        mapper_registry.map_imperatively(self.LoginHistory, user_login_history)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Если в таблице активных пользователей есть записи, то их необходимо удалить
        self.session.query(self.ActiveUsers).delete()
        self.session.commit()

       # Функция выполняющяяся при входе пользователя, записывает в базу факт входа
    def user_login(self, username, ip_address, port, key):
        # Запрос в таблицу пользователей на наличие там пользователя с таким именем
        rez = self.session.query(self.Client_table).filter_by(name=username)

        # Если имя пользователя уже присутствует в таблице, обновляем время последнего входа
        if rez.count():
            user = rez.first()
            user.last_login = datetime.datetime.now()
            if user.pubkey != key:
                user.pubkey = key
        else:
            raise ValueError('Пользователь не зарегистрирован.')
        # Если нету, то создаздаём нового пользователя
        # Теперь можно создать запись в таблицу активных пользователей о факте
        # входа.
        new_active_user = self.ActiveUsers(
            user.id, ip_address, port, datetime.datetime.now())
        self.session.add(new_active_user)

        # и сохранить в историю входов
        history = self.LoginHistory(
            user.id, datetime.datetime.now(), ip_address, port)
        self.session.add(history)

        # Сохрраняем изменения
        self.session.commit()

    def add_user(self, name, passwd_hash):
        '''
        Метод регистрации пользователя.
        Принимает имя и хэш пароля, создаёт запись в таблице статистики.
        '''
        user_row = self.Client_table(name, passwd_hash)
        self.session.add(user_row)
        self.session.commit()
        history_row = self.UsersHistory(user_row.id)
        self.session.add(history_row)
        self.session.commit()


    def remove_user(self, name):
        '''Метод удаляющий пользователя из базы.'''
        user = self.session.query(self.Client_table).filter_by(name=name).first()
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()
        self.session.query(self.LoginHistory).filter_by(name=user.id).delete()
        self.session.query(self.Contact_list).filter_by(user=user.id).delete()
        self.session.query(
            self.Contact_list).filter_by(
            contact=user.id).delete()
        self.session.query(self.UsersHistory).filter_by(user=user.id).delete()
        self.session.query(self.Client_table).filter_by(name=name).delete()
        self.session.commit()


    def get_hash(self, name):
        '''Метод получения хэша пароля пользователя.'''
        user = self.session.query(self.Client_table).filter_by(name=name).first()
        return user.passwd_hash

    def get_pubkey(self, name):
        '''Метод получения публичного ключа пользователя.'''
        user = self.session.query(self.Client_table).filter_by(name=name).first()
        return user.pubkey

    def check_user(self, name):
        '''Метод проверяющий существование пользователя.'''
        if self.session.query(self.Client_table).filter_by(name=name).count():
            return True
        else:
            return False

    def user_logout(self, username):
        # Запрашиваем пользователя, что покидает нас
        user = self.session.query(self.Client_table).filter_by(name=username).first()

        # Удаляем его из таблицы активных пользователей.
        self.session.query(self.ActiveUsers).filter_by(user=user.id).delete()

        # Применяем изменения
        self.session.commit()


        # Функция фиксирует передачу сообщения и делает соответствующие отметки в БД
    def process_message(self, sender, recipient):
        # Получаем ID отправителя и получателя
        sender = self.session.query(self.Client_table).filter_by(name=sender).first().id
        recipient = self.session.query(self.Client_table).filter_by(name=recipient).first().id
        # Запрашиваем строки из истории и увеличиваем счётчики
        sender_row = self.session.query(self.UsersHistory).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.UsersHistory).filter_by(user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()

        # Функция возвращает список активных пользователей
    def active_users_list(self):
    # Запрашиваем соединение таблиц и собираем кортежи имя, адрес, порт, время.
        query = self.session.query(
            self.Client_table.name,
            self.ActiveUsers.ip_address,
            self.ActiveUsers.port,
            self.ActiveUsers.login_time
        ).join(self.Client_table)
        # Возвращаем список кортежей
        return query.all()


    def login_history(self, username=None):
        '''Метод возвращающий историю входов.'''
        # Запрашиваем историю входа
        query = self.session.query(self.Client_table.name,
                                   self.LoginHistory.date_time,
                                   self.LoginHistory.ip,
                                   self.LoginHistory.port
                                   ).join(self.Client_table)
        # Если было указано имя пользователя, то фильтруем по нему
        if username:
            query = query.filter(self.Client_table.name == username)
        # Возвращаем список кортежей
        return query.all()


        # Функция возвращает список контактов пользователя.
    def get_contacts(self, username):
        # Запрашивааем указанного пользователя
        user = self.session.query(self.Client_table).filter_by(name=username).one()

        # Запрашиваем его список контактов
        query = self.session.query(self.Contact_list, self.Client_table.name). \
            filter_by(user=user.id). \
            join(self.Client_table, self.Contact_list.contact == self.Client_table.id)

        # выбираем только имена пользователей и возвращаем их.
        return [contact[1] for contact in query.all()]


    def add_contact(self, user, contact):
        # Получаем ID пользователей
        user = self.session.query(self.Client_table).filter_by(name=user).first()
        contact = self.session.query(self.Client_table).filter_by(name=contact).first()

        # Проверяем что не дубль и что контакт может существовать (полю пользователь мы доверяем)
        if not contact or self.session.query(self.Contact_list).filter_by(user=user.id, contact=contact.id).count():
            return

        # Создаём объект и заносим его в базу
        contact_row = self.Contact_list(user.id, contact.id)
        self.session.add(contact_row)
        self.session.commit()


    def remove_contact(self, user, contact):
        # Получаем ID пользователей
        user = self.session.query(self.Client_table).filter_by(name=user).first()
        contact = self.session.query(self.Client_table).filter_by(name=contact).first()

        # Проверяем что контакт может существовать (полю пользователь мы доверяем)
        if not contact:
            return

        # Удаляем требуемое
        print(self.session.query(self.Contact_list).filter(
            self.Contact_list.user == user.id,
            self.Contact_list.contact == contact.id
        ).delete())
        self.session.commit()


            # Функция возвращает список известных пользователей со временем последнего входа.
    def users_list(self):
        # Запрос строк таблицы пользователей.
        query = self.session.query(
            self.Client_table.name,
            self.Client_table.last_login
        )
        # Возвращаем список кортежей
        return query.all()
    

    # Функция возвращает количество переданных и полученных сообщений
    def message_history(self):
        query = self.session.query(
            self.Client_table.name,
            self.Client_table.last_login,
            self.UsersHistory.sent,
            self.UsersHistory.accepted
        ).join(self.Client_table)
        # Возвращаем список кортежей
        return query.all()


# if __name__ == '__main__':
#     test_db = ServerDB()
#     test_db.user_login('1111', '192.168.1.113', 8080)
#     test_db.user_login('McG2', '192.168.1.113', 8081)
#     print(test_db.users_list())
#     # print(test_db.active_users_list())
#     # test_db.user_logout('McG')
#     # print(test_db.login_history('re'))
#     # test_db.add_contact('test2', 'test1')
#     # test_db.add_contact('test1', 'test3')
#     # test_db.add_contact('test1', 'test6')
#     # test_db.remove_contact('test1', 'test3')
#     test_db.process_message('McG2', '1111')
#     print(test_db.message_history())
