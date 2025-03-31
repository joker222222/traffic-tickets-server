from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey,Time, DateTime
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session
from datetime import datetime
from config import Config

# Инициализация базы данных
DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI
engine = create_engine(DATABASE_URL, echo=True)
Base = declarative_base()

# Создаём фабрику сессий
Session = scoped_session(sessionmaker(bind=engine))

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    registration_date = Column(DateTime, default=datetime.now)
    role_id = Column(Integer, ForeignKey("roles.id"), default=1)

    role = relationship("Role", back_populates="users")


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    name = Column(String)

    users = relationship("User", back_populates="role")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    question_count = Column(Integer)
    time_limit = Column(Integer)


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    text = Column(Text)
    image = Column(String)
    answer_options = Column(Text)
    correct_answer = Column(Text)
    explanation = Column(Text)


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    correct_questions = Column(Text)

    user = relationship("User")
    ticket = relationship("Ticket")


class SupportChat(Base):
    __tablename__ = "support_chat"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)

    user = relationship("User")


class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    news_id = Column(Integer, ForeignKey("news.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    reaction = Column(String)

    user = relationship("User")
    news = relationship("News")


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    image = Column(String)
    text = Column(Text)
    dislikes = Column(Integer)
    likes = Column(Integer)

    likes_relationship = relationship("Like", back_populates="news")


class TicketQuestion(Base):
    __tablename__ = "ticket_questions"

    id = Column(Integer, primary_key=True, unique=True, nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))

    ticket = relationship("Ticket")
    question = relationship("Question")

Base.metadata.create_all(engine)