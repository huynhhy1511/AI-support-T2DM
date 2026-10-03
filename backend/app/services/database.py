import logging
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import engine

logger = logging.getLogger(__name__)


def check_database_connection(db: Optional[Session] = None) -> bool:
    """Verify connectivity to PostgreSQL by executing 'SELECT 1'.

    Args:
        db: Optional active SQLAlchemy Session. If not provided, a temporary
            engine connection will be established.

    Returns:
        bool: True if connection is successful, False otherwise without crashing.
    """
    if db is not None:
        try:
            result = db.execute(text("SELECT 1")).scalar()
            return result == 1
        except Exception as exc:
            logger.warning("Database session connectivity check failed: %s", exc)
            return False

    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            return result == 1
    except Exception as exc:
        logger.warning("Database engine connectivity check failed: %s", exc)
        return False
