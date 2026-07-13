from sqlalchemy import Column, Integer, String, Date
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True)
    email = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    password = Column(String)
    enroller_id = Column(String)
    date_of_birth = Column(Date)
    country = Column(String)
    city = Column(String)
    zip_code = Column(String)
    mobile = Column(String)
    aadhar_no = Column(String)
    gender = Column(String)
    club = Column(String)
    role = Column(String, default="USER")