from sqlalchemy import create_engine, event
from django.conf import settings


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