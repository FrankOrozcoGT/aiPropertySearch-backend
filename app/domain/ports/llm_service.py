"""LLM Service Port - Contract for language model integration"""
from abc import ABC, abstractmethod


class ILLMService(ABC):
    """
    Port (interface) for generating SQL from natural language queries.
    
    Any LLM integration (Ollama, OpenAI, etc.) must comply with this contract.
    """

    @abstractmethod
    async def generate_sql(self, query: str) -> str:
        """
        Generate SQL query from natural language query.
        
        Args:
            query: Natural language search query from user
            
        Returns:
            SQL SELECT query
            
        Raises:
            ValueError: If query is empty or invalid
            RuntimeError: If LLM connection fails or times out
        """
        pass

    @abstractmethod
    async def validate_sql(self, sql: str) -> bool:
        """
        Validate if SQL is safe to execute.
        
        Args:
            sql: SQL query to validate
            
        Returns:
            True if SQL is valid and safe
            
        Raises:
            ValueError: If SQL is dangerous (injection attack, etc.)
        """
        pass
