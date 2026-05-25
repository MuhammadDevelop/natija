from logging.config import fileConfig
# pyrefly: ignore [missing-import]
from sqlalchemy import engine_from_config, pool
from alembic import context

# alembic.ini dan logging sozlamalarini o'qiymiz
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Barcha modellarni import qilamiz
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import Base  # noqa: F401 - barcha modellar shu orqali yuklanadi
from app.core.config import settings

# Alembic URL ni .env dan olish
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Offline rejimda migratsiyalarni ishlatish."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Online rejimda migratsiyalarni ishlatish."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
