from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import pool
from logging.config import fileConfig
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Импорт моделей
from database.models import Base

# Логирование
fileConfig(context.config.config_file_name)

# URL базы данных
url = "postgresql+asyncpg://botcanal:botcanal@localhost:5432/botcanal"

# Асинхронный движок
engine = create_async_engine(
    url,
    poolclass=pool.NullPool,
)

# Метаданные
target_metadata = Base.metadata

def run_migrations_offline():
    """Офлайн-миграции"""
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online():
    """Онлайн-миграции"""
    async with engine.connect() as connection:
        # Настройка контекста
        await connection.run_sync(
            lambda conn: context.configure(
                connection=conn,
                target_metadata=target_metadata,
                compare_type=True,
            )
        )

        # Запуск миграций
        await connection.run_sync(lambda conn: context.run_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())