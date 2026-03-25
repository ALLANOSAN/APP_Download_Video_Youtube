from sqlmodel import SQLModel, create_engine, Session
import os

# Obtém a URL do banco das variáveis de ambiente ou usa SQLite como padrão local
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./sync_data.db")

# Ajuste para compatibilidade com o Neon/Render (PostgreSQL)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Argumentos extras apenas para SQLite
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
