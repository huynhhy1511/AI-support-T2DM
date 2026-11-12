import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


def get_user_by_id(db: Session, user_id: uuid.UUID) -> Optional[User]:
    """Retrieve user by UUID."""
    stmt = select(User).where(User.id == user_id)
    return db.scalars(stmt).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieve user by email address."""
    stmt = select(User).where(User.email == email.lower().strip())
    return db.scalars(stmt).first()


def list_users(db: Session, skip: int = 0, limit: int = 50) -> List[User]:
    """List users with pagination."""
    stmt = select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def create_user(db: Session, user_in: UserCreate) -> User:
    """Create a new user with consent tracking."""
    consent_at = datetime.now(timezone.utc) if user_in.consent_accepted else None
    user = User(
        email=user_in.email.lower().strip(),
        display_name=user_in.display_name.strip() if user_in.display_name else None,
        consent_accepted_at=consent_at,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: uuid.UUID, user_in: UserUpdate) -> Optional[User]:
    """Update user profile information."""
    user = get_user_by_id(db, user_id)
    if not user:
        return None

    if user_in.display_name is not None:
        user.display_name = user_in.display_name.strip() if user_in.display_name else None

    if user_in.consent_accepted is not None:
        if user_in.consent_accepted and not user.consent_accepted_at:
            user.consent_accepted_at = datetime.now(timezone.utc)
        elif not user_in.consent_accepted:
            user.consent_accepted_at = None

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: uuid.UUID) -> bool:
    """Delete a user and cascading relationships."""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True

