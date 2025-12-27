"""Pytest configuration and fixtures"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.base import Base
from app.core.config import settings


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine"""
    # Use a test database URL if available, otherwise use the default
    test_db_url = settings.DATABASE_URL.replace("/miniatures_erp", "/miniatures_erp_test")
    engine = create_engine(test_db_url)
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Drop all tables after tests
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_db_engine):
    """Create a new database session for a test"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestingSessionLocal()
    
    yield session
    
    session.rollback()
    session.close()
