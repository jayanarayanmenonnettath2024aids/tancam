import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/unifyops.db")

if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def bulk_upsert(session, model, records, index_elements):
    """
    Performs UPSERT (ON CONFLICT DO UPDATE).
    Works for both SQLite and PostgreSQL backends.
    """
    if not records:
        return

    dialect = session.bind.dialect.name
    
    if dialect == "postgresql":
        stmt = pg_insert(model).values(records)
        update_dict = {c.name: c for c in stmt.excluded if c.name not in index_elements}
        if update_dict:
            stmt = stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_=update_dict
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)
    elif dialect == "sqlite":
        stmt = sqlite_insert(model).values(records)
        update_dict = {c.name: c for c in stmt.excluded if c.name not in index_elements}
        if update_dict:
            stmt = stmt.on_conflict_do_update(
                index_elements=index_elements,
                set_=update_dict
            )
        else:
            stmt = stmt.on_conflict_do_nothing(index_elements=index_elements)
    else:
        # Fallback
        session.bulk_insert_mappings(model, records)
        session.commit()
        return

    session.execute(stmt)
    session.commit()
