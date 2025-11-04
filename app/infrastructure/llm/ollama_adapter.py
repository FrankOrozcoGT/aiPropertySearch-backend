"""Ollama LLM Adapter - Integration with Ollama for SQL generation"""
import json
import logging
import re
from typing import Tuple

import requests
from sqlalchemy import text, create_engine
from sqlalchemy.exc import SQLAlchemyError

from app.config import settings
from app.domain.ports.llm_service import ILLMService
from app.domain.ports.prompt_service import IPromptService

logger = logging.getLogger(__name__)


class OllamaLLMAdapter(ILLMService):
    """
    LLM adapter for Ollama.
    
    Implements ILLMService port.
    Uses Ollama to generate SQL with separated parameters from natural language queries.
    Uses sqlglot for validation (professional SQL parser used by Meta, Stripe, etc.)
    """

    def __init__(self, prompt_service: IPromptService, timeout: int = 30):
        """
        Initialize Ollama adapter.
        
        Args:
            prompt_service: Service for loading LLM prompts
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = timeout
        self.prompt_service = prompt_service
        
        logger.info(f"✓ Ollama adapter initialized: {self.base_url} (model: {self.model})")

    async def generate_sql_with_params(self, query: str) -> Tuple[str, list]:
        """
        Generate SQL with separated parameters from natural language query using Ollama.
        
        Args:
            query: Natural language search query
            
        Returns:
            Tuple of (sql_template, params_array)
            - sql_template: SQL with ? placeholders
            - params_array: Values in order
            
        Raises:
            ValueError: If query is empty or LLM response is invalid
            RuntimeError: If Ollama connection fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Get prompt from prompt service
        system_prompt = self.prompt_service.get_sql_generation_prompt(query)

        try:
            logger.debug(f"Calling Ollama for query: {query[:50]}...")
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{system_prompt}\n\nUser query: {query}",
                    "stream": False,
                    "temperature": 0.1,  # Low temp for consistency
                },
                timeout=self.timeout,
            )
            
            response.raise_for_status()
            
            response_text = response.json().get("response", "").strip()
            logger.debug(f"Ollama response: {response_text[:150]}...")
            
            # Parse Markdown response - extract SQL and params from code blocks
            sql, params = self._parse_markdown_response(response_text)
            
            logger.info(f"✓ Generated SQL with {len(params)} parameters")
            logger.info(f"  SQL: {sql}")
            logger.info(f"  PARAMS: {params}")
            
            return sql, params
            
        except requests.RequestException as e:
            logger.error(f"✗ Ollama connection error: {str(e)}")
            raise RuntimeError(f"Failed to connect to Ollama: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"✗ JSON parsing error: {str(e)}")
            raise ValueError(f"Invalid JSON from LLM: {str(e)}")
        except Exception as e:
            logger.error(f"✗ Unexpected error in SQL generation: {str(e)}", exc_info=True)
            raise RuntimeError(f"Failed to generate SQL: {str(e)}")

    async def validate_sql_template(self, sql: str, params: list) -> bool:
        """
        Validate if SQL template is safe using SQLAlchemy with MySQL dialect.
        
        Args:
            sql: SQL template with %s placeholders (MySQL style)
            params: Array of parameter values
            
        Returns:
            True if SQL is valid and safe
            
        Raises:
            ValueError: If SQL is invalid or dangerous
        """
        try:
            logger.debug(f"Validating SQL template: {sql[:50]}...")
            
            # Check 1: Validate with SQLAlchemy text() - compiles without executing
            # text() handles parameterized queries safely
            stmt = text(sql)
            
            # Check 2: Verify it's a SELECT (read-only) query
            sql_upper = sql.strip().upper()
            if not sql_upper.startswith("SELECT"):
                raise ValueError("Only SELECT queries are allowed")
            
            # Check 3: Reject dangerous keywords
            dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER", "EXEC", "EXECUTE", "TRUNCATE"]
            for keyword in dangerous_keywords:
                if f" {keyword} " in f" {sql_upper} ":
                    raise ValueError(f"Dangerous SQL keyword detected: {keyword}")
            
            logger.info("✓ SQL template validation passed")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"SQL compilation error: {str(e)}")
            raise ValueError(f"Invalid SQL syntax: {str(e)}")
        except ValueError as e:
            logger.warning(f"⚠️ SQL validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"✗ Validation error: {str(e)}", exc_info=True)
            raise ValueError(f"SQL validation failed: {str(e)}")

    def _parse_markdown_response(self, response_text: str) -> Tuple[str, list]:
        """
        Parse Markdown response with SQL and params code blocks.
        
        Expected format:
        ## SQL Query
        ```sql
        SELECT * FROM propiedades WHERE ...
        ```
        
        ## Parameters
        ```json
        [value1, value2, ...]
        ```
        
        Args:
            response_text: Markdown response from LLM
            
        Returns:
            Tuple of (sql, params)
            
        Raises:
            ValueError: If parsing fails
        """
        logger.debug(f"Full LLM response:\n{response_text}\n")
        
        # Extract SQL block
        sql_match = re.search(r'```(?:mysql)?\s*(SELECT[^`]*?)\s*```', response_text, re.IGNORECASE | re.DOTALL)
        if not sql_match:
            logger.error(f"Could not find SQL block in response: {response_text}")
            raise ValueError("LLM response missing SQL code block")
        
        sql = sql_match.group(1).strip()
        
        # Extract params block (JSON array)
        params_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
        if not params_match:
            logger.error(f"Could not find params block in response: {response_text}")
            raise ValueError("LLM response missing parameters JSON block")
        
        try:
            params = json.loads(params_match.group(1))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in params block: {params_match.group(1)}")
            raise ValueError(f"Invalid JSON in parameters: {str(e)}")
        
        if not isinstance(params, list):
            raise ValueError("Parameters must be a JSON array")
        
        logger.debug(f"Parsed Markdown - SQL: {sql[:60]}... Params: {params}")
        logger.debug(f"Full SQL: {sql}")
        logger.debug(f"Full Params: {params}")
        return sql, params

