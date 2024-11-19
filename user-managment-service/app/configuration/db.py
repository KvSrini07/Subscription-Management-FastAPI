import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.models.models import Base

# Load environment variables from .env file
load_dotenv()

# Environment variables for database connection
DATABASE_URL = os.getenv('DATABASE_URL')

# Asynchronous engine for MySQL with aiomysql
engine = create_async_engine(
    DATABASE_URL,
    echo=True,             # Enable SQL query logging
    pool_size=10,          # Set the pool size
    max_overflow=20,       # Allow overflow connections if pool is full
    pool_timeout=60,       # Timeout in seconds before failing
    pool_recycle=1800      # Recycle connections after 30 minutes
)

# Create an async session bound to the engine
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Initialize the database schema (run once to create tables)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Connection Manager to handle sessions
class ConnectionManager:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        if self.session is None:
            self.session = AsyncSessionLocal()
        return self.session

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self.session:
            await self.session.close()
            self.session = None
