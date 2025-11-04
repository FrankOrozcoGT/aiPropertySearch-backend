"""Property Repository Port - Contract for property data access"""
from abc import ABC, abstractmethod
from typing import Any


class IPropertyRepository(ABC):
    """
    Port (interface) for accessing property data.
    
    Any implementation (MySQL, PostgreSQL, etc.) must comply with this contract.
    """

    @abstractmethod
    async def search(self, sql: str) -> list[dict[str, Any]]:
        """
        Execute a search query and return results.
        
        Args:
            sql: SQL SELECT query to execute
            
        Returns:
            List of property records as dictionaries
            
        Raises:
            ValueError: If SQL is invalid or dangerous
            RuntimeError: If database connection fails
        """
        pass
