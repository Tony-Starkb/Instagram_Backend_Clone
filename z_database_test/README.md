# SQLAlchemy Tutorial for This Project

This folder is a safe playground for learning how SQLAlchemy works in a real backend system.

## 1) What is SQLAlchemy?

SQLAlchemy is the standard Python ORM and database toolkit used in production-grade backends.

It helps you:

- talk to PostgreSQL, MySQL, SQLite, Oracle, and more
- write Python instead of raw SQL in most places
- map Python classes to database tables
- manage sessions, transactions, and connection pools
- keep your app clean and maintainable

In real production systems, SQLAlchemy is usually used with:

- FastAPI for API endpoints
- PostgreSQL for the main database
- Alembic for migrations
- Pydantic for request/response validation

---

## 2) Main SQLAlchemy pieces you must know

### Engine

The engine is the connection manager.

Example:

```python
engine = create_engine("sqlite:///app.db", echo=True)
```

It does not represent one connection. It manages a pool of connections.

### Session

The session is the main object you use to:

- add rows
- update rows
- query rows
- commit changes
- rollback on error

Example:

```python
with Session(engine) as session:
    session.add(user)
    session.commit()
```

### Declarative Base

This is the base class for your ORM models.

Example:

```python
class Base(DeclarativeBase):
    pass
```

### ORM Model

A Python class mapped to a table.

Example:

```python
class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    email = Column(String, nullable=False, unique=True)
```

### Query API

You use `select()` to query data.

Example:

```python
stmt = select(User).where(User.username == "john")
result = session.execute(stmt).scalar_one_or_none()
```

### Relationship

Used when one table references another.

Example:

```python
class Post(Base):
    user_id = Column(String, ForeignKey("users.id"))
    user = relationship("User", back_populates="posts")
```

---

## 3) Core libraries/modules used in real systems

You will normally use these:

- `sqlalchemy`: core ORM toolkit
- `sqlalchemy.orm`: Session, DeclarativeBase, Mapped, mapped_column, relationship
- `sqlalchemy.engine`: Engine, create_engine
- `sqlalchemy.schema`: Column, ForeignKey
- `sqlalchemy.types`: String, Integer, Boolean, DateTime, Text
- `sqlalchemy.exc`: IntegrityError, SQLAlchemyError
- `psycopg[binary]`: PostgreSQL driver
- `python-dotenv`: load `.env` values
- `alembic`: migrations
- `fastapi`: API layer
- `pydantic`: validation layer

---

## 4) Production setup checklist

Use this checklist when building a real application:

### Step 1 — Install packages

```bash
pip install SQLAlchemy==2.0.30 psycopg[binary]==3.2.0 python-dotenv==1.0.0 alembic==1.13.1
```

### Step 2 — Create environment variables

Example `.env`:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/instacore
```

### Step 3 — Create a database engine

Use one engine for the whole app.

### Step 4 — Create a session factory

Use `sessionmaker(bind=engine)`.

### Step 5 — Define your ORM models

Keep models in a `models/` or `schemas/` package.

### Step 6 — Create tables

Use `Base.metadata.create_all(bind=engine)` for development.
For production use Alembic migrations.

### Step 7 — Use sessions via dependency injection

In FastAPI:

```python
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 8 — Use transactions carefully

- `session.commit()` saves changes
- `session.rollback()` reverses failed changes

### Step 9 — Add migrations

Use Alembic when your schema changes in production.

### Step 10 — Add indexes and constraints

This is very important for Instagram-scale systems:

- unique indexes on email/username
- foreign keys for relations
- indexes on `created_at`, `username`, `user_id`

---

## 5) Why this is better than raw JSON files

Raw JSON works for learning, but real production systems need:

- transactions
- concurrency control
- indexes
- relational integrity
- safe updates and deletes
- faster reads/writes at scale

SQLAlchemy gives you those foundations.

---

## 6) Production architecture pattern

A clean pattern is:

1. Router receives request
2. Router validates input with Pydantic
3. Router calls `db_handler` or service layer
4. Service uses a SQLAlchemy session
5. SQLAlchemy writes to PostgreSQL
6. Response is converted back to Pydantic schema

This is the same pattern used in large real-world systems.

---

## 7) Example: real project flow

### Create user

```python
new_user = User(
    id=str(uuid.uuid4()),
    email="user@example.com",
    username="user1",
    password_hash="hashed_password",
    full_name="User One",
)

session.add(new_user)
session.commit()
```

### Query user

```python
stmt = select(User).where(User.username == "user1")
user = session.execute(stmt).scalar_one_or_none()
```

### Update user

```python
user.full_name = "Updated Name"
session.commit()
```

### Delete user

```python
session.delete(user)
session.commit()
```

---

## 8) Best practices for production

- never expose `password_hash` in API responses
- always hash passwords before saving
- use `select()` instead of raw SQL when possible
- use `SessionLocal()` per request
- close sessions in `finally`
- configure connection pool settings
- always use transactions
- use migrations instead of manual SQL changes
- add indexes for frequently queried columns

---

## 9) Files in this folder

- `01_sqlalchemy_basics.py` → simple learning example with SQLite
- `02_postgres_production_pattern.py` → production-style template for PostgreSQL

---

## 10) How to use these examples

1. Run the basics example first
2. Read the production template second
3. Copy the pattern into your real `db_handler.py`
4. Replace SQLite with PostgreSQL URL
5. Add Alembic migrations later

This folder is intentionally separated from the main app so you can experiment safely.
