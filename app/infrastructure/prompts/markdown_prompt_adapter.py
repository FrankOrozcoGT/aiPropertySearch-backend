"""Prompt Service Adapter - Load prompts from markdown files"""
import json
import logging
import os
from app.domain.ports.prompt_service import IPromptService

logger = logging.getLogger(__name__)


class MarkdownPromptAdapter(IPromptService):
    """
    Loads LLM prompts from markdown files.
    
    Implements IPromptService port.
    Decouples prompt content from LLM logic.
    """

    def __init__(self, prompts_dir: str = None):
        """
        Initialize prompt adapter.
        
        Args:
            prompts_dir: Directory containing prompt markdown files
        """
        if prompts_dir is None:
            # Default to app/infrastructure/prompts (same directory as this file)
            prompts_dir = os.path.dirname(__file__)
        
        self.prompts_dir = prompts_dir
        self._prompt_cache = {}
        
        logger.info(f"✓ Markdown prompt adapter initialized at: {self.prompts_dir}")

    def get_sql_generation_prompt(self, query: str) -> str:
        """
        Get the SQL generation prompt with user query interpolated.
        
        Args:
            query: User's natural language query
            
        Returns:
            Formatted prompt with query inserted
        """
        prompt_content = self._load_prompt("sql_generation.md")
        return prompt_content.format(query=query)

    def get_fix_sql_parameters_prompt(self, query: str, sql: str, params: list, 
                                       error: str = None, placeholder_count: int = None) -> str:
        """
        Get the fix SQL prompt for correcting SQL errors.
        
        Args:
            query: User's original natural language query
            sql: The generated SQL template with %s placeholders
            params: Current parameters array
            error: Error message from SQLAlchemy validation
            placeholder_count: Number of %s placeholders in SQL (legacy param)
            
        Returns:
            Formatted prompt for LLM to fix SQL
        """
        prompt_content = self._load_prompt("fix_sql_parameters.md")
        
        return prompt_content.format(
            query=query,
            sql=sql,
            params=json.dumps(params),
            error=error or "Unknown error"
        )

    def _load_prompt(self, filename: str) -> str:
        """
        Load a prompt from a markdown file with caching.
        
        Args:
            filename: Name of the prompt file (e.g., "sql_generation.md")
            
        Returns:
            Content of the prompt file
            
        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        if filename in self._prompt_cache:
            return self._prompt_cache[filename]
        
        filepath = os.path.join(self.prompts_dir, filename)
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Prompt file not found: {filepath}")
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            
            self._prompt_cache[filename] = content
            logger.debug(f"Loaded prompt: {filename}")
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to load prompt {filename}: {str(e)}")
            raise
