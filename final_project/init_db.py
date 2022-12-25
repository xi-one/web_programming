from email.quoprimime import unquote
from enum import unique
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

# initialize db information

mysql_url = "mysql+pymysql://root:ID@localhost/test?charset=utf8"  # connecting to mysql db
engine = create_engine(mysql_url)

db_session = scoped_session(sessionmaker(
    autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = db_session.query_property()

class User(Base): # user infomation
    __tablename__ = 'User'
    id = Column(Integer, primary_key=True)
    email = Column(String(50), unique=True)
    passwd = Column(String(50))
    name = Column(String(50))
    major = Column(String(50))
    studentid = Column(String(50))

    def __init__(self, email=None, passwd=None, name=None, major=None, studentid=None):
        self.email = email
        self.passwd = passwd
        self.name = name
        self.major = major
        self.studentid = studentid

    def __repr__(self):
        return 'User %s, %r, %r, %r, %r' % (self.id, self.email, self.name, self.major, self.studentid)


class Post(Base):  # posts for club or suggestion information
    __tablename__ = 'Post'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    username = Column(String(50))
    title = Column(String(100))
    content = Column(String(1500))
    created_at = Column(String(50))
    required_signature_num = Column(Integer)
    signature_num = Column(Integer)
    board = Column(String(50))

    def __init__(self, user_id=None, username=None, title=None, content=None, create_at=None, required_signature_num=None, signature_num=None, board=None):
        self.user_id = user_id
        self.username = username
        self.title = title
        self.content = content
        self.created_at = create_at
        self.required_signature_num = required_signature_num
        self.signature_num = signature_num
        self.board = board


class Notice(Base):  # information of notice post
    __tablename__ = 'Notice'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    username = Column(String(50))
    title = Column(String(100))
    content = Column(String(1500))
    created_at = Column(String(50))

    def __init__(self, user_id=None, username=None, title=None, content=None, create_at=None):
        self.user_id = user_id
        self.username = username
        self.title = title
        self.content = content
        self.created_at = create_at




class Signature(Base):  #  information of signature files
    __tablename__ = 'Signature'
    id = Column(Integer, primary_key=True)
    post_id = Column(Integer)
    user_id = Column(Integer)

    def __init__(self, post_id=None, user_id=None):
        self.post_id = post_id
        self.user_id = user_id



def init_database():
    Base.metadata.create_all(bind=engine)