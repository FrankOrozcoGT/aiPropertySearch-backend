"""Property Repository Port - Contract for property data access"""
from abc import ABC, abstractmethod
from typing import Any


class IPropertyRepository(ABC):
    """
    Port (interface) for accessing property data.
    
    Any implementation (MySQL, PostgreSQL, etc.) must comply with this contract.
    Executes parameterized queries for maximum security.
    """

    @abstractmethod
    async def search(self, sql: str, params: list) -> list[dict[str, Any]]:
        """
        Execute a parameterized search query and return results.
        
        Args:
            sql: SQL SELECT query template with ? placeholders
            params: Array of parameter values matching placeholders
            
        Returns:
            List of property records as dictionaries
            
        Raises:
            ValueError: If SQL structure is invalid
            RuntimeError: If database connection fails
        """
        pass
