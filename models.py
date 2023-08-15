from sqlalchemy import Column, DateTime, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class Contact(Base):
    __tablename__ = "contact"

    id = Column(Integer, index=True, primary_key=True)
    phoneNumber = Column(String)
    email = Column(String)
    linkedId = Column(Integer)
    linkPrecedence = Column(String)
    createdAt = Column(DateTime)
    updatedAt = Column(DateTime)
    deletedAt = Column(DateTime)


Base.metadata.create_all(engine)
