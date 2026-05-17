from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.database import Base

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(255))
    report = Column(Text)
    trends = Column(Text)
    competitors = Column(Text)
    sources = Column(Text)  # lưu dạng JSON string
    created_at = Column(DateTime, default=datetime.now)