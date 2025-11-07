import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Exemplo de URL (combine com seu docker-compose):
# postgresql+psycopg2://chatuser:chatpass@postgres:5432/chat4all
DATABASE_URL = os.getenv(
    "DB_URL",
    "postgresql+psycopg2://chatuser:chatpass@postgres:5432/chat4all"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # verifica conexões antes de usar
    future=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()
