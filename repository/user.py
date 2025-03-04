from sqlalchemy.orm import Session
from sqlalchemy import Column, LargeBinary, Integer, String, LargeBinary
# from attr import define

from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    password = Column(String)
    email = Column(String, unique=True, index=True)
    foto = Column(LargeBinary, nullable=True)


# @define
# class UserCreate:
#     email: str
#     password: str
#     name: str


class UserRepository:
    def find_user_by_email(self, db: Session, email: str):
        return db.query(User).filter(User.email == email).first()
    
    def add(self, db:Session, user: User)-> User:
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
        
    def get_all(self, db:Session, skip: int = 0, limit: int = 100):
        return db.query(User).offser(skip).limit(limit).all()

    def find_user_by_id(self, db:Session, id: int):
        return db.query(User).filter(User.id == id).first()
        