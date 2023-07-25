from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users1'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String)
    city = Column(String)

    def __repr__(self):
        return f"<User(name='{self.name}', email='{self.email}')>"

