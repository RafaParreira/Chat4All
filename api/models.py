from sqlalchemy import Column, String, Text
from .db import Base

class Message(Base):
    __tablename__ = "messages"

    message_id = Column(String(64), primary_key=True)
    conversation_id = Column(String(64))
    sender = Column(String(64))
    receiver = Column(Text)
    payload = Column(Text)
    status = Column(String(32))