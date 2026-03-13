"""Initialize database: create tables + seed default admin user.

Usage:
    python -m scripts.init_db
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app.models import *  # noqa: F401,F403  — register all models


def init():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

    db = SessionLocal()
    try:
        from app.models.user import User, UserRole

        existing = db.query(User).filter_by(username="admin").first()
        if existing:
            print("Admin user already exists, skipping seed.")
        else:
            admin = User(
                username="admin",
                hashed_password=hash_password("admin123"),
                name="系统管理员",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print("Default admin created: username=admin, password=admin123")
            print(">>> IMPORTANT: Change the admin password after first login! <<<")
    finally:
        db.close()


if __name__ == "__main__":
    init()
