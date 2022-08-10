import asyncio

from sqlalchemy import Column, Integer, String, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, AsyncEngine, AsyncConnection
from sqlalchemy.orm import declarative_base, sessionmaker
from random import Random
import string
from validators import url as url_validate
from typing import Optional, Any, Callable

rng = Random()
MAX_LENGTH = 5
BASE_64 = string.ascii_letters + string.digits + '-' + '%'
base_len = len(BASE_64)

def get_code_for(num: int) -> tuple[bool, str]:
    if not isinstance(num, int):
        return (False, None)
    
    res_idx: list[int] = list()
    while num > 0:
        res_idx.append(num % base_len)
        num = num // base_len
    
    return (True, ''.join(
            map(
                lambda i: BASE_64[i],
                res_idx[::-1]
            )
        )
    )

def decode(code: str) -> tuple[bool, int]:
    if any(map(lambda x: x not in BASE_64, code)):
        return (False, -1)
    
    indices = list(map(
        lambda c: BASE_64.index(c),
        code
    ))
    current_power = 0
    base = len(BASE_64)
    number = 0
    for i in indices[::-1]:
        number += i * pow(base, current_power)
        current_power += 1
    
    return (True, number)

Base = declarative_base()

class UrlRecordModel(Base):
    __tablename__ = 'shortened_urls'
    
    USED_NUMBERS: set[int] = set()

    id = Column(Integer, primary_key=True)
    url = Column(String)

    def __init__(self, id: int, url: str, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.id = id
        self.url = url

    @classmethod
    def CreateNew(cls, url: str) -> tuple[Optional[str], Optional['UrlRecordModel']]:
        if not url_validate(url):
            return (None, None)

        number = rng.randint(1, base_len) 
        while number in cls.USED_NUMBERS:
            number = rng.randint(1, base_len) 
        
        cls.USED_NUMBERS.add(number)
        valid, code = get_code_for(number)
        
        if not valid:
            return (None, None)
        else:
            return (code, UrlRecordModel(number, url))

engine: Optional[AsyncEngine] = None
async_session = None

async def async_db_start() -> AsyncSession:
    global engine, async_session

    engine = create_async_engine(
        "sqlite+aiosqlite:///test.sqlite",
        echo=True,
        future=True
    )

    async with engine.begin() as conn:
        conn: AsyncConnection
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    return async_session()

Session = asyncio.run(async_db_start())

async def close_connection() -> None:
    if engine != None:
        await engine.dispose()