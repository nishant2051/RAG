"""Migrations share the application's validated SQLite engine and metadata."""

from alembic import context

from app.infrastructure.database import Base, engine


def run_migrations_offline() -> None:
    context.configure(
        url=engine.url, target_metadata=Base.metadata,
        literal_binds=True, dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
