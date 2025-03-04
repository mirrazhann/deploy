from sqlalchemy.orm import Session

from sqlalchemy import Column, Integer, String, Float

from database import Base

class Flower(Base):
    __tablename__ = "flowers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    price = Column(Float)
    count = Column(Integer)


class FlowerRepository:

    def add(self, db: Session, flower: Flower):
        db.add(flower)
        db.commit()
        db.refresh(flower)
        return flower.id

    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(Flower).offset(skip).limit(limit).all()
    
    def get_by_id(self, db: Session, id: int):
        return db.query(Flower).filter(Flower.id == id).first()
    
    def update(self, db: Session, flower: Flower):
        db.commit()
        db.refresh(flower)
        return flower.id
    
    
    def delete(self, db: Session, flower: Flower):
        db.delete(flower)
        db.commit()
        return 
    



