import datetime
from sqlalchemy import DateTime, Text, create_engine, Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import registry, sessionmaker




class ClientDB:
    class Users:
        def __init__(self, user):
            self.id = None
            self.username = user
    

    class MessageHistory:
        def __init__(self, from_user, to_user, message):
            self.id = None
            self.from_user = from_user
            self.to_user = to_user
            self.message = message
            self.date = datetime.datetime.now()


    class Contacts:
        def __init__(self, contact):
            self.id = None
            self.name = contact


    def __init__(self, name):
        self.engine = create_engine(f'sqlite:///{name}.db3', echo=False, pool_recycle=7200,
                                             connect_args={'check_same_thread': False})

        self.metadata = MetaData()

        users = Table('users', self.metadata,
                      Column('id', Integer, primary_key=True),
                      Column('username', String)
                      )
        
        history = Table('message_history', self.metadata,
                        Column('id', Integer, primary_key=True),
                        Column('from_user', String),
                        Column('to_user', String),
                        Column('message', Text),
                        Column('date', DateTime)
                        )
        
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

    # Функция добавления контактов
    def add_contact(self, contact):
        if not self.session.query(self.Contacts).filter_by(name=contact).count():
            contact_row = self.Contacts(contact)
            self.session.add(contact_row)
            self.session.commit()

    # Функция удаления контакта
    def del_contact(self, contact):
        self.session.query(self.Contacts).filter_by(name=contact).delete()

    # Функция добавления известных пользователей.
    # Пользователи получаются только с сервера, поэтому таблица очищается.
    def add_users(self, users_list):
        self.session.query(self.Users).delete()
        for user in users_list:
            user_row = self.Users(user)
            self.session.add(user_row)
        self.session.commit()

    # Функция сохраняющяя сообщения
    def save_message(self, from_user, to_user, message):
        message_row = self.MessageHistory(from_user, to_user, message)
        self.session.add(message_row)
        self.session.commit()

    # Функция проверяющяя наличие пользователя в известных
    def check_user(self, user):
        if self.session.query(self.Users).filter_by(username=user).count():
            return True
        else:
            return False
        
    # Функция возвращающяя контакты
    def get_contacts(self):
        return [contact[0] for contact in self.session.query(self.Contacts.name).all()]

    # Функция возвращающяя список известных пользователей
    def get_users(self):
        return [user[0] for user in self.session.query(self.Users.username).all()]

    # Функция проверяющяя наличие пользователя контактах
    def check_contact(self, contact):
        if self.session.query(self.Contacts).filter_by(name=contact).count():
            return True
        else:
            return False