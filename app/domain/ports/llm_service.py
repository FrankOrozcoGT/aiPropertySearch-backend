"""LLM Service Port - Contract for language model integration"""
from abc import ABC, abstractmethod
from typing import Tuple


class ILLMService(ABC):
    """
    Port (interface) for generating SQL from natural language queries.
    
    Any LLM integration (Ollama, OpenAI, etc.) must comply with this contract.
    Generates parameterized queries with separated values for maximum security.
    """

    @abstractmethod
    async def generate_sql_with_params(self, query: str) -> Tuple[str, list]:
        """
        Generate SQL query with separated parameters.
        
        Args:
            query: Natural language search query from user
            
        Returns:
            Tuple of (sql_template, params_array)
            - sql_template: SQL with ? placeholders (e.g., "SELECT * FROM propiedades WHERE precio < ?")
            - params_array: Array of values in order (e.g., [500000])
            
        Raises:
            ValueError: If query is empty or invalid
            RuntimeError: If LLM connection fails or times out
        """
        pass

    @abstractmethod
    async def validate_sql_template(self, sql: str, params: list) -> bool:
        """
        Validate if SQL template is safe to execute.
        
        Args:
            sql: SQL template with ? placeholders (no literal values)
            params: Array of parameter values
            
        Returns:
            True if SQL is valid and safe
            
        Raises:
            ValueError: If SQL is dangerous or structure is invalid
        """
        pass
