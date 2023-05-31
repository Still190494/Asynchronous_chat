import datetime
from sqlalchemy import DateTime, create_engine, Table, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import registry, sessionmaker

engine = create_engine('sqlite:///server_db.db3', echo=True, pool_recycle=7200)
metadata = MetaData()


client_table = Table('users', metadata,
Column('id', Integer, primary_key=True),
Column('username', String, unique=True),
Column('info', String),
)


history_client_table = Table('history_client', metadata,
Column('id', Integer, primary_key=True),
Column('id_client', ForeignKey('users.id')),
Column('time_login', DateTime),
Column('ip', Integer),
)


contact_list_table = Table('contact_list', metadata,
Column('id', Integer, primary_key=True),
Column('id_client', ForeignKey('users.id')),
Column('id_owner', ForeignKey('users.id')),
)


metadata.create_all(engine)
mapper_registry = registry()

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


client_map = mapper_registry.map_imperatively(Client_table, client_table)
history_map = mapper_registry.map_imperatively(History_client, history_client_table)
contact_map = mapper_registry.map_imperatively(Contact_list, contact_list_table)


Session = sessionmaker(bind=engine)
session = Session()



