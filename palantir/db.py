from sqlalchemy import create_engine

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Float,
    Integer,
    String,
)


Base = declarative_base()


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    coin = Column(String)
    vs_currency = Column(String)
    timestamp = Column(Integer)
    price = Column(Float)


def init_db():
    engine = create_engine('sqlite:///quotes.db', echo=True)

    Base.metadata.create_all(engine)

    return engine
