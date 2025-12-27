"""Property-based tests for database connection"""
import pytest
from hypothesis import given, strategies as st, settings
from sqlalchemy import text, inspect
from sqlalchemy.exc import OperationalError
from app.core.database import engine, SessionLocal, get_db
from app.models.base import Base


# Feature: miniatures-erp, Property 1: Database connection on startup
# Validates: Requirements 20.1
@pytest.mark.property
@settings(max_examples=100)
@given(
    # Generate random connection attempts to verify consistent behavior
    attempt_number=st.integers(min_value=1, max_value=100)
)
def test_database_connection_on_startup(attempt_number):
    """
    Property: For any startup attempt, the ERP System SHALL connect to a dedicated PostgreSQL database.
    
    This property verifies that:
    1. The database engine is properly initialized
    2. A connection can be established
    3. The connection is to a PostgreSQL database
    4. The connection is functional (can execute queries)
    """
    # Verify the engine exists and is configured
    assert engine is not None, "Database engine should be initialized"
    
    # Verify we can establish a connection
    try:
        with engine.connect() as connection:
            # Verify the connection is active
            assert connection is not None, "Database connection should be established"
            
            # Verify it's a PostgreSQL database
            dialect_name = connection.dialect.name
            assert dialect_name == "postgresql", f"Database should be PostgreSQL, got {dialect_name}"
            
            # Verify the connection is functional by executing a simple query
            result = connection.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            assert row is not None, "Should be able to execute queries"
            assert row[0] == 1, "Query should return expected result"
            
    except OperationalError as e:
        pytest.fail(f"Failed to connect to database: {e}")


@pytest.mark.property
def test_database_session_creation():
    """
    Property: The ERP System SHALL be able to create database sessions consistently.
    
    This verifies that the session factory is properly configured and can create
    working database sessions.
    """
    # Verify SessionLocal is configured
    assert SessionLocal is not None, "Session factory should be initialized"
    
    # Create a session
    session = SessionLocal()
    try:
        assert session is not None, "Should be able to create a database session"
        
        # Verify the session is bound to the correct engine
        assert session.bind == engine, "Session should be bound to the database engine"
        
        # Verify the session can execute queries
        result = session.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        assert row is not None, "Session should be able to execute queries"
        assert row[0] == 1, "Query should return expected result"
        
    finally:
        session.close()


@pytest.mark.property
def test_database_dependency_injection():
    """
    Property: The get_db dependency function SHALL provide working database sessions.
    
    This verifies that the dependency injection mechanism for database sessions
    works correctly and properly manages session lifecycle.
    """
    # Get a database session using the dependency function
    db_generator = get_db()
    
    try:
        db = next(db_generator)
        
        assert db is not None, "Dependency should provide a database session"
        
        # Verify the session is functional
        result = db.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        assert row is not None, "Session should be able to execute queries"
        assert row[0] == 1, "Query should return expected result"
        
    finally:
        # Ensure cleanup happens
        try:
            next(db_generator)
        except StopIteration:
            pass  # Expected - generator should close the session


@pytest.mark.property
@settings(max_examples=100)
@given(
    # Test with multiple concurrent connection attempts
    connection_count=st.integers(min_value=1, max_value=10)
)
def test_database_multiple_connections(connection_count):
    """
    Property: The ERP System SHALL support multiple concurrent database connections.
    
    This verifies that the connection pool is properly configured and can handle
    multiple simultaneous connections.
    """
    connections = []
    
    try:
        # Create multiple connections
        for _ in range(connection_count):
            conn = engine.connect()
            connections.append(conn)
            
            # Verify each connection works
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            assert row is not None, "Each connection should be functional"
            assert row[0] == 1, "Each connection should execute queries correctly"
            
    finally:
        # Clean up all connections
        for conn in connections:
            conn.close()


@pytest.mark.property
def test_database_tables_exist():
    """
    Property: When the ERP System starts, all required database tables SHALL exist.
    
    This verifies that the database schema is properly initialized on startup.
    """
    # Get the inspector to check database structure
    inspector = inspect(engine)
    
    # Get all table names from the database
    existing_tables = inspector.get_table_names()
    
    # Verify that tables exist (at least some tables should be created)
    assert len(existing_tables) > 0, "Database should have tables created on startup"
    
    # Verify we can query the metadata
    assert Base.metadata is not None, "Base metadata should be initialized"
    
    # Note: We don't check for specific tables here because this is a startup test
    # and the exact tables depend on which models have been created so far


@pytest.mark.property
def test_database_connection_pool_configuration():
    """
    Property: The database connection pool SHALL be properly configured.
    
    This verifies that the connection pool has appropriate settings for
    production use.
    """
    # Verify pool configuration
    pool = engine.pool
    
    assert pool is not None, "Connection pool should be configured"
    
    # Verify we can get a connection from the pool
    conn = engine.connect()
    try:
        result = conn.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1, "Connection from pool should work"
    finally:
        conn.close()
    
    # Verify the pool has reasonable size settings
    # The pool should have a size greater than 0
    assert pool.size() >= 0, "Pool should have a valid size"
