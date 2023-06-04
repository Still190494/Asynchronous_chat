import datetime
from sqlalchemy import DateTime, create_engine, Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import registry, sessionmaker

class ServerDB:
    class Client_table:
        def __init__(self, username, info):
            self.id = None
            self.username = username
            self.info = info


    class History_client:
        def __init__(self, ip):
            self.id = None
            self.time_login = datetime.datetime.now()
            self.ip = ip


    class Contact_list:
        def __init__(self, id_client, id_owner):
            self.id_client = id_client
            self.id_owner = id_owner


    class ActiveUsers:
        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None


    def __init__(self):
        self.engine = create_engine('sqlite:///server_db.db3', echo=True, pool_recycle=7200, connect_args={'check_same_thread': False})
        self.metadata = MetaData()
        """Таблица всех пользователей"""
        client_table = Table('users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('username', String, unique=True),
                            Column('info', String),
                            )

        """Таблица истории пользователя"""
        history_client_table = Table('history_client', self.metadata,
                                    Column('id', Integer, primary_key=True),
                                    Column('id_client', ForeignKey('users.id')),
                                    Column('time_login', DateTime),
                                    Column('ip', String),
                                    )

        """Список контактов"""
        contact_list_table = Table('contact_list', self.metadata,
                                Column('id', Integer, primary_key=True),
                                Column('id_client', ForeignKey('users.id')),
                                Column('id_owner', ForeignKey('users.id')),
                                )

        """Таблица активных пользователей"""
        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('users.id'), unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime)
                                   )

        self.metadata.create_all(self.engine)
        mapper_registry = registry()
        mapper_registry.map_imperatively(self.Client_table, client_table)
        mapper_registry.map_imperatively(self.History_client, history_client_table)
        mapper_registry.map_imperatively(self.Contact_list, contact_list_table)
        mapper_registry.map_imperatively(self.ActiveUsers, active_users_table)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()


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
        sender_row = self.session.query(self.History_client).filter_by(user=sender).first()
        sender_row.sent += 1
        recipient_row = self.session.query(self.History_client).filter_by(user=recipient).first()
        recipient_row.accepted += 1

        self.session.commit()   


        # Функция возвращает список контактов пользователя.
    def get_contacts(self, username):
        # Запрашивааем указанного пользователя
        user = self.session.query(self.Client_table).filter_by(name=username).one()

        # Запрашиваем его список контактов
        query = self.session.query(self.Contact_list, self.Client_table.username). \
            filter_by(user=user.id). \
            join(self.Client_table, self.Contact_list.id_owner == self.Client_table.id)

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
            self.Contact_list.id_client == user.id,
            self.Contact_list.id_owner == contact.id
        ).delete())
        self.session.commit()


            # Функция возвращает список известных пользователей со временем последнего входа.
    def users_list(self):
        # Запрос строк таблицы пользователей.
        query = self.session.query(
            self.Client_table.username,
            self.Client_table.info
        )
        # Возвращаем список кортежей
        return query.all()





test = ServerDB()
print(test)
