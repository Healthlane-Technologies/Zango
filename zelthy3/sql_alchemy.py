from sqlalchemy import create_engine, event
from django.conf import settings


from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# db = settings.DATABASES['default']

db = {
    'USER': 'postgres',
    'PASSWORD': 'zelthy3pass',
    'HOST': 'localhost',
    'NAME': 'postgres'
}   

engine = create_engine('postgresql://%s:%s@%s/%s'%(
                                    db['USER'], 
                                    db['PASSWORD'],
                                    db['HOST'],
                                    db['NAME']
                                    ))


@event.listens_for(engine, "connect")
def set_search_path(dbapi_connection, connection_record):
    from django.db import connection
    cursor = dbapi_connection.cursor()
    cursor.execute("SET search_path TO %s, public"%(connection.tenant.name))
    cursor.close()


class Singleton_sa:
    _instance = None
    base = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance
    
sa_base = Singleton_sa()

from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
class SingletonModelMeta(DeclarativeMeta):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        print("----------", cls.__table__.name)
        if cls.__table__.name in cls._instances:
            return cls._instances[cls.__table__.name]
        instance = super().__call__(*args, **kwargs)
        cls._instances[cls.__table__.name] = instance
        return instance

Base = declarative_base(metaclass=SingletonModelMeta)