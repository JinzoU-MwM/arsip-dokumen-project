"""
Database connection and session management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.declarative import declarative_base
import structlog
from contextlib import contextmanager
from typing import Generator

logger = structlog.get_logger()

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/legal_automation"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
    future=True,
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error("Database transaction error", error=str(e))
        session.rollback()
        raise
    finally:
        session.close()


class DatabaseManager:
    """Database manager class for handling connections and operations"""

    def __init__(self, database_url: str = None):
        self.database_url = database_url or DATABASE_URL
        self.engine = create_engine(
            self.database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
            future=True,
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            future=True,
        )
        self.logger = structlog.get_logger().bind(component="DatabaseManager")

    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()

    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Context manager for database sessions with automatic commit/rollback"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            self.logger.error("Database session error", error=str(e))
            session.rollback()
            raise
        finally:
            session.close()

    def create_tables(self):
        """Create all database tables"""
        try:
            from .models import Base
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Database tables created successfully")
        except Exception as e:
            self.logger.error("Failed to create database tables", error=str(e))
            raise

    def drop_tables(self):
        """Drop all database tables (use with caution!)"""
        try:
            from .models import Base
            Base.metadata.drop_all(bind=self.engine)
            self.logger.warning("All database tables dropped")
        except Exception as e:
            self.logger.error("Failed to drop database tables", error=str(e))
            raise

    def check_connection(self) -> bool:
        """Check if database connection is working"""
        try:
            with self.session_scope() as session:
                session.execute("SELECT 1")
            self.logger.info("Database connection check successful")
            return True
        except Exception as e:
            self.logger.error("Database connection check failed", error=str(e))
            return False

    def get_database_info(self) -> dict:
        """Get database information and statistics"""
        try:
            with self.session_scope() as session:
                # Get table counts
                result = {}

                # Users count
                from .models import User
                result["users_count"] = session.query(User).count()

                # Companies count
                from .models import Company
                result["companies_count"] = session.query(Company).count()

                # Documents count
                from .models import Document
                result["documents_count"] = session.query(Document).count()

                # Processing jobs count
                from .models import ProcessingJob
                result["processing_jobs_count"] = session.query(ProcessingJob).count()

                # Notifications count
                from .models import Notification
                result["notifications_count"] = session.query(Notification).count()

                # Audit logs count
                from .models import AuditLog
                result["audit_logs_count"] = session.query(AuditLog).count()

                return result

        except Exception as e:
            self.logger.error("Failed to get database info", error=str(e))
            return {}


# Global database manager instance
db_manager = DatabaseManager()