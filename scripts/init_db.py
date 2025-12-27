"""Initialize database and create initial migration"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import engine
from app.models.base import Base
# Import all models to ensure they're registered
from app.models import (
    order, product, customer, payment, painter,
    inventory, expense, invoice
)


def init_db():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_db()
