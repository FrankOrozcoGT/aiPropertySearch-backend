"""Port for loading and managing LLM prompts"""
from abc import ABC, abstractmethod


class IPromptService(ABC):
    """
    Port (interface) for loading and managing LLM prompts.
    
    Decouples prompt content from LLM adapter logic.
    """

    @abstractmethod
    def get_sql_generation_prompt(self, query: str) -> str:
        """
        Get the system prompt for SQL generation.
        
        Args:
            query: User's natural language query
            
        Returns:
            System prompt for initial SQL generation
        """
        pass

    @abstractmethod
    def get_fix_sql_parameters_prompt(self, query: str, sql: str, params: list, 
                                       error: str = None, placeholder_count: int = None) -> str:
        """
        Get the prompt for fixing SQL query errors.
        
        Args:
            query: User's original natural language query
            sql: Generated SQL template with %s placeholders
            params: Current parameters array
            error: Error message from SQLAlchemy validation
            placeholder_count: Number of %s placeholders in SQL (optional, for legacy)
            
        Returns:
            Prompt for LLM to fix SQL errors
        """
        pass
