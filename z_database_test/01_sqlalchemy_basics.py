"""Basic SQLAlchemy example using SQLite.

This file is for learning only. It shows the core SQLAlchemy pieces:
- create_engine
- DeclarativeBase
- mapped_column
- Session
- select
- commit/rollback
"""

from datetime import datetime

from sqlalchemy import String, DateTime, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


engine = create_engine("sqlite:///z_database_test_demo.db", echo=False)
Base.metadata.create_all(bind=engine)


def create_user(email: str, username: str, full_name: str) -> None:
    with Session(engine) as session:
        user = User(email=email, username=username, full_name=full_name)
        session.add(user)
        session.commit()
        print("Created user:", user.id, user.username)


def list_users() -> None:
    with Session(engine) as session:
        stmt = select(User).order_by(User.created_at.desc())
        users = session.execute(stmt).scalars().all()
        for user in users:
            print("USER:", user.id, user.email, user.username)


if __name__ == "__main__":
    create_user("demo1@example.com", "demo1", "Demo User One")
    create_user("demo2@example.com", "demo2", "Demo User Two")
    list_users()
