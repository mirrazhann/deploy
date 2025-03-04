from sqlalchemy.orm import Session
from sqlalchemy import Column, Text, Integer

from database import Base

class Purchase(Base):
    __tablename__ = "purchase"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    flowers = Column(Text)

class PurchaseRepository:

    def add(self, db: Session, purchase: Purchase):
        db.add(purchase)
        db.commit()
        db.refresh(purchase)
        return purchase

    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(Purchase).offset(skip).limit(limit).all()
    
    def get_by_user_id(self, db: Session, user_id: int):
        return db.query(Purchase).filter(user_id == user_id).all()
    



