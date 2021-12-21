from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

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
    """
    Connect to the db and if necessary initialise the schema.
    """
    engine = create_engine("sqlite:///quotes.db", echo=False)

    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    return session


def drop_all():
    """
    Delete all structures in this database.
    """
    engine = create_engine("sqlite:///quotes.db", echo=False)
    Base.metadata.drop_all(engine)
