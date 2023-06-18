import datetime
import os

from sqlalchemy import DateTime, Text, create_engine, Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import registry, sessionmaker


class ClientDB:
    """Класс создания и взаимодействия с клиентской базой данных"""

    class Users:
        """Класс отображения таблицы пользователей"""

        def __init__(self, user):
            self.id = None
            self.username = user

    class MessageHistory:
        """Класс отображения таблицы истории сообщений"""

        def __init__(self, from_user, to_user, message):
            self.id = None
            self.from_user = from_user
            self.to_user = to_user
            self.message = message
            self.date = datetime.datetime.now()

    class Contacts:
        """Класс отображения таблицы контактов пользователей"""

        def __init__(self, contact):
            self.id = None
            self.name = contact

    def __init__(self, name):
        """Конструктор класса, создающий базу данных клиентов"""
        path = os.path.dirname(os.path.realpath(__file__))
        filename = f'client_{name}.db3'
        self.engine = create_engine(f'sqlite:///{os.path.join(path, filename)}', echo=False, pool_recycle=7200,
                                    connect_args={'check_same_thread': False})

        self.metadata = MetaData()

        # Таблица пользователей
        users = Table('users', self.metadata,
                      Column('id', Integer, primary_key=True),
                      Column('username', String)
                      )
        # Таблица истории сообщений
        history = Table('message_history', self.metadata,
                        Column('id', Integer, primary_key=True),
                        Column('from_user', String),
                        Column('to_user', String),
                        Column('message', Text),
                        Column('date', DateTime)
                        )
        # Таблица контактов пользователей
        contacts = Table('contacts', self.metadata,
                         Column('id', Integer, primary_key=True),
                         Column('name', String, unique=True)
                         )

        self.metadata.create_all(self.engine)
        mapper_registry = registry()
        mapper_registry.map_imperatively(self.Users, users)
        mapper_registry.map_imperatively(self.MessageHistory, history)
        mapper_registry.map_imperatively(self.Contacts, contacts)

        Session = sessionmaker(bind=self.engine)
        self.session = Session()

        # Необходимо очистить таблицу контактов, т.к. при запуске они подгружаются с сервера.
        self.session.query(self.Contacts).delete()
        self.session.commit()

    def add_contact(self, contact):
        """Метод добавлений контактов"""
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    def del_contact(self, contact):
        """Метод удаления контактов"""
        self.session.query(self.Contacts).filter_by(name=contact).delete()

    def contacts_clear(self):
        """Метод очищающий таблицу со списком контактов"""
        self.session.query(self.Contacts).delete()

    def add_users(self, users_list):
        """Метод создания таблицы зарегистрированных пользователей"""
        self.session.query(self.Users).delete()
        for user in users_list:
            user_row = self.Users(user)
            self.session.add(user_row)
        self.session.commit()

    def save_message(self, from_user, to_user, message):
        """Метод сохранения сообщений"""
        message_row = self.MessageHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()

    def check_user(self, user):
        """Метод проверки существования пользователя"""
        if self.session.query(self.Users).filter_by(username=user).count():
            return True
        else:
            return False

    def get_contacts(self):
        """Метод возвращающий список контактов"""
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    def get_users(self):
        """Метод возвращающий список зарегистрированных пользователей"""
        return [user[0] for user in self.session.query(self.Users.username).all()]

    def check_contact(self, contact):
        """Метод проверки существования контакта"""
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False

    def get_history(self, from_who=None, to_who=None):
        """Метод возвращающий историю сообщений"""
        query = self.session.query(self.MessageHistory)
        return [(history_row.from_user, history_row.to_user, history_row.message, history_row.date)
                for history_row in query.all()]
