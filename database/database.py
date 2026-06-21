

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
import os   
from typing import Generator


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")



engine = create_engine(
    DATABASE_URL, 
    pool_pre_ping=True, 
    echo=False
)
SessionLocal = sessionmaker(
    bind=engine, 
    autoflush=False, 
    autocommit=False,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    
    
def drop_tables() -> None:
    Base.metadata.drop_all(bind=engine)
    
    
def reset_tables():
    drop_tables()
    create_tables()
    

def check_connection() -> bool:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as e:
        print("Database connection error:", e)
        return False