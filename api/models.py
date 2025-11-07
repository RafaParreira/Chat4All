from sqlalchemy import Column, String, Text, Index
from db import Base

class Message(Base):
    __tablename__ = "messages"

    message_id = Column(String(64), primary_key=True)
    conversation_id = Column(String(64), index=True)
    sender = Column(String(64), index=True)
    receiver = Column(Text)
    payload = Column(Text)
    status = Column(String(32))  # 'SENT' | 'DELIVERED' etc.

# Índices adicionais (úteis para listar por conversa + ordenação no SQL)
Index("idx_messages_conversation", Message.conversation_id)
Index("idx_messages_sender", Message.sender)
