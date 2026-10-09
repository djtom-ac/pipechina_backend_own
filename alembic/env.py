from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
import asyncio
from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
import app.bootstrap.model_registry  # noqa: F401
from app.bootstrap.config import get_settings
from app.shared.db import Base
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# target_metadata = None
config.set_main_option("sqlalchemy.url", get_settings().database_url)    # 动态读取  动态配置
target_metadata = Base.metadata
# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """--sql 生成脚本：换成同步驱动，asyncpg 不支持离线模式。"""
    url = get_settings().database_url.replace("+asyncpg", "+psycopg2")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """同步函数：context 必须在这里配，run_sync 会提供 greenlet 上下文。"""
    context.configure(connection=connection, target_metadata=target_metadata,include_schemas=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = create_async_engine(
        get_settings().database_url,
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:   # ← async with
        await connection.run_sync(do_run_migrations)  # ← 核心
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
