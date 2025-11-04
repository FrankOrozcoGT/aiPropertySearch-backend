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
            - sql_template: SQL with %s placeholders
            - params_array: Values in order
            
        Raises:
            ValueError: If query is empty or LLM response is invalid
            RuntimeError: If Ollama connection fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Store query for use in fix attempts
        self._last_query = query

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
        Attempts to fix errors up to 3 times if validation fails.
        
        Args:
            sql: SQL template with %s placeholders (MySQL style)
            params: Array of parameter values
            
        Returns:
            True if SQL is valid and safe
            
        Raises:
            ValueError: If SQL is invalid or dangerous after 3 fix attempts
        """
        max_retries = 3
        current_sql = sql
        current_params = params
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"Validating SQL template (attempt {attempt + 1}/{max_retries}): {current_sql[:50]}...")
                
                # Check 1: Validate with SQLAlchemy text() - compiles without executing
                stmt = text(current_sql)
                
                # Check 2: Verify it's a SELECT (read-only) query
                sql_upper = current_sql.strip().upper()
                if not sql_upper.startswith("SELECT"):
                    raise ValueError("Only SELECT queries are allowed")
                
                # Check 3: Reject dangerous keywords
                dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER", "EXEC", "EXECUTE", "TRUNCATE"]
                for keyword in dangerous_keywords:
                    if f" {keyword} " in f" {sql_upper} ":
                        raise ValueError(f"Dangerous SQL keyword detected: {keyword}")
                
                logger.info("✓ SQL template validation passed")
                return True
                
            except (SQLAlchemyError, ValueError) as e:
                error_msg = str(e)
                logger.warning(f"⚠️ SQL validation failed (attempt {attempt + 1}/{max_retries}): {error_msg}")
                
                # If last attempt, raise the error
                if attempt == max_retries - 1:
                    logger.error(f"✗ SQL validation failed after {max_retries} attempts: {error_msg}")
                    raise ValueError(f"SQL validation failed: {error_msg}")
                
                # Try to fix the SQL with LLM
                logger.info(f"🔧 Attempting to fix SQL with LLM...")
                try:
                    current_sql, current_params = await self._fix_sql_with_llm(
                        original_query=getattr(self, '_last_query', 'unknown'),
                        sql=current_sql,
                        params=current_params,
                        error=error_msg
                    )
                    logger.info(f"✓ Fixed SQL: {current_sql[:60]}...")
                except Exception as fix_error:
                    logger.error(f"✗ Could not fix SQL: {str(fix_error)}")
                    # Continue to next retry or raise if last attempt
                    if attempt == max_retries - 1:
                        raise ValueError(f"SQL validation failed and could not be fixed: {error_msg}")
            
            except Exception as e:
                logger.error(f"✗ Unexpected validation error: {str(e)}", exc_info=True)
                raise ValueError(f"SQL validation failed: {str(e)}")
        
        return False

    async def _fix_sql_with_llm(self, original_query: str, sql: str, params: list, error: str) -> Tuple[str, list]:
        """
        Use LLM to fix SQL query that failed validation.
        
        Args:
            original_query: Original user query
            sql: Broken SQL template
            params: Current parameters
            error: Error message from SQLAlchemy
            
        Returns:
            Tuple of (fixed_sql, fixed_params)
        """
        fix_prompt = self.prompt_service.get_fix_sql_parameters_prompt(
            query=original_query,
            sql=sql,
            params=params,
            error=error
        )
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": fix_prompt,
                    "stream": False,
                    "temperature": 0.1,
                },
                timeout=self.timeout,
            )
            
            response.raise_for_status()
            response_text = response.json().get("response", "").strip()
            
            # Parse fixed SQL and params
            fixed_sql, fixed_params = self._parse_markdown_response(response_text)
            
            logger.info(f"✓ LLM fixed SQL: {fixed_sql[:60]}...")
            logger.info(f"  Params: {fixed_params}")
            
            return fixed_sql, fixed_params
            
        except Exception as e:
            logger.error(f"✗ LLM fix failed: {str(e)}")
            raise RuntimeError(f"Could not fix SQL with LLM: {str(e)}")

    def _parse_markdown_response(self, response_text: str) -> Tuple[str, list]:
        """
        Parse Markdown response from LLM to extract WHERE clause and parameters.
        Then builds complete SQL query with fixed SELECT, FROM, and GROUP BY.
        
        Expected format (from new prompt):
        ### WHERE Clause
        ```
        propiedades.tipo = %s AND propiedades.habitaciones = %s AND propiedades.estado = 'activa'
        ```
        
        ### Parameters
        ```json
        ["casa", 3]
        ```
            
        Returns:
            Tuple of (complete_sql, params)
            
        Raises:
            ValueError: If parsing fails
        """
        logger.debug(f"Full LLM response:\n{response_text}\n")
        
        # Extract WHERE clause
        where_match = re.search(r'### WHERE Clause\s*```\s*(.*?)\s*```', response_text, re.IGNORECASE | re.DOTALL)
        if not where_match:
            logger.error(f"Could not find WHERE clause in response: {response_text}")
            raise ValueError("LLM response missing WHERE clause")
        
        where_clause = where_match.group(1).strip()
        
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
        
        # Build complete SQL query with fixed SELECT, FROM, and GROUP BY
        complete_sql = f"""SELECT 
  propiedades.id,
  propiedades.titulo,
  propiedades.descripcion,
  propiedades.tipo,
  propiedades.precio,
  propiedades.habitaciones,
  propiedades.banos,
  propiedades.area_m2,
  propiedades.ubicacion,
  propiedades.zona_administrativa,
  propiedades.fecha_publicacion,
  GROUP_CONCAT(DISTINCT a.tipo ORDER BY a.tipo) as amenidades_tipos,
  GROUP_CONCAT(DISTINCT CONCAT(a.nombre, ' (', pa.distancia_km, 'km)') ORDER BY pa.distancia_km) as amenidades_cercanas
FROM propiedades
LEFT JOIN propiedades_amenidades pa ON propiedades.id = pa.propiedad_id
LEFT JOIN amenidades a ON pa.amenidad_id = a.id
WHERE {where_clause}
GROUP BY propiedades.id
ORDER BY propiedades.fecha_publicacion DESC"""
        
        logger.debug(f"Parsed Markdown - WHERE: {where_clause[:60]}... Params: {params}")
        logger.debug(f"Full SQL: {complete_sql}")
        logger.debug(f"Full Params: {params}")
        return complete_sql, params

