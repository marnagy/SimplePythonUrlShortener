import asyncio

from sqlalchemy import Column, Integer, String, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, selectinload, sessionmaker


Base = declarative_base()

class UrlRecordModel(Base):
    __tablename__ = 'shortened_urls'

    id = Column(Integer, primary_key=True)
    url = Column(String)

    @classmethod
    def CreateNew(url: str) -> UrlRecordModel:
        pass
