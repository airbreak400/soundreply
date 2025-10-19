from datetime import datetime
from typing import Optional
from sqlalchemy import String, BigInteger, Integer, DateTime, select, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255))
    first_name: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    search_count: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)


class SearchLog(Base):
    __tablename__ = "search_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger)
    query: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


class DatabaseManager:
    @staticmethod
    async def get_or_create_user(user_id: int, username: str = None, 
                                  first_name: str = None) -> User:
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(
                    id=user_id,
                    username=username,
                    first_name=first_name
                )
                session.add(user)
            else:
                user.last_active = datetime.utcnow()
                user.username = username
                user.first_name = first_name
            
            await session.commit()
            await session.refresh(user)
            return user
    
    @staticmethod
    async def log_search(user_id: int, query: str):
        async with async_session() as session:
            # Qidiruvni saqlash
            search_log = SearchLog(user_id=user_id, query=query)
            session.add(search_log)
            
            # Foydalanuvchi statistikasini yangilash
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.search_count += 1
                user.last_active = datetime.utcnow()
            
            await session.commit()
    
    @staticmethod
    async def increment_sent_count(user_id: int):
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.sent_count += 1
                await session.commit()
    
    @staticmethod
    async def get_statistics():
        async with async_session() as session:
            total_users = await session.execute(select(func.count(User.id)))
            total_searches = await session.execute(select(func.sum(User.search_count)))
            total_sent = await session.execute(select(func.sum(User.sent_count)))
            
            return {
                "total_users": total_users.scalar() or 0,
                "total_searches": total_searches.scalar() or 0,
                "total_sent": total_sent.scalar() or 0
            }