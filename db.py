from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "postgresql://postgres:yourpassword@localhost:5433/mini_uber"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Ride(Base):
    __tablename__ = "rides"

    ride_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    pickup = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    status = Column(String, default="pending")

def init_db():
    Base.metadata.create_all(bind=engine)
