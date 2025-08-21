import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

Base = declarative_base()


class Chat(Base):
    """SQLAlchemy model for a chat session."""

    __tablename__ = "chats"
    id = Column(Integer, primary_key=True)
    name = Column(
        String, default=f"Chat-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    )
    messages = relationship(
        "Message", back_populates="chat", cascade="all, delete-orphan"
    )


class Message(Base):
    """SQLAlchemy model for a single message within a chat."""

    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    content = Column(String)
    is_user = Column(Boolean)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    chat = relationship("Chat", back_populates="messages")


engine = create_engine("sqlite:///chat_history.db")
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)


def create_session():
    return Session()
