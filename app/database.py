"""Database Connection - MySQL connection management"""
import logging
from typing import AsyncGenerator

import mysql.connector
from mysql.connector import Error, CMySQLConnection

from app.config import settings

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages MySQL database connections with support for parameterized queries"""

    def __init__(self):
        self._connection: CMySQLConnection | None = None

    async def connect(self) -> None:
        """
        Establish connection to MySQL database.
        
        Raises:
            RuntimeError: If connection fails
        """
        try:
            logger.debug(f"Attempting connection to MySQL: host={settings.DB_HOST}, port={settings.DB_PORT}, user={settings.DB_USER}, db={settings.DB_NAME}")
            
            self._connection = mysql.connector.connect(
                host=settings.DB_HOST,
                port=int(settings.DB_PORT),
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                autocommit=True,
                use_pure=True,
            )
            
            if not self._connection.is_connected():
                raise RuntimeError("Failed to connect to MySQL")
            
            logger.info(f"✓ Connected to MySQL: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
            
        except Error as e:
            logger.error(f"✗ MySQL connection error: {str(e)}")
            raise RuntimeError(f"Database connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """Close database connection"""
        if self._connection and self._connection.is_connected():
            self._connection.close()
            logger.info("✓ Disconnected from MySQL")

    def get_connection(self) -> CMySQLConnection:
        """
        Get current connection.
        
        Returns:
            MySQL connection
            
        Raises:
            RuntimeError: If not connected
        """
        if not self._connection or not self._connection.is_connected():
            raise RuntimeError("Database not connected. Call connect() first.")
        
        return self._connection

    async def execute_query(self, sql: str) -> list[dict]:
        """
        Execute a SELECT query and return results as dictionaries.
        (Deprecated: use execute_query_with_params for security)
        
        Args:
            sql: SELECT query to execute
            
        Returns:
            List of result rows as dictionaries
            
        Raises:
            ValueError: If SQL is invalid
            RuntimeError: If query execution fails
        """
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True, buffered=True)
            
            logger.debug(f"Executing query: {sql[:100]}...")
            cursor.execute(sql)
            
            results = cursor.fetchall()
            logger.info(f"✓ Query executed successfully, returned {len(results)} rows")
            
            return results
            
        except Error as e:
            logger.error(f"✗ SQL execution error: {str(e)}")
            raise RuntimeError(f"Failed to execute query: {str(e)}")
            
        finally:
            if cursor:
                cursor.close()

    async def execute_query_with_params(self, sql: str, params: list) -> list[dict]:
        """
        Execute a parameterized SELECT query and return results as dictionaries.
        RECOMMENDED: Uses mysql-connector's built-in parameter escaping for security.
        
        Args:
            sql: SELECT query template with %s placeholders (MySQL style)
            params: Array of parameter values
            
        Returns:
            List of result rows as dictionaries
            
        Raises:
            ValueError: If SQL is invalid
            RuntimeError: If query execution fails
        """
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=True, buffered=True)
            
            logger.debug(f"Executing parameterized query: {sql[:100]}... with {len(params)} params")
            logger.debug(f"  Params: {params}")
            
            # mysql-connector automatically escapes parameters when tuple is passed
            cursor.execute(sql, tuple(params))
            
            results = cursor.fetchall()
            logger.info(f"✓ Query executed successfully, returned {len(results)} rows")
            
            return results
            
        except Error as e:
            logger.error(f"✗ SQL execution error: {str(e)}")
            raise RuntimeError(f"Failed to execute query: {str(e)}")
            
        finally:
            if cursor:
                cursor.close()

    async def health_check(self) -> bool:
        """
        Check if database is healthy and connected.
        
        Returns:
            True if connected and healthy
        """
        try:
            if not self._connection or not self._connection.is_connected():
                return False
            
            # Test with simple query
            cursor = self._connection.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            return True
            
        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            return False


# Singleton database connection
db_connection = DatabaseConnection()
