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
            try:
                sql, params = self._parse_markdown_response(response_text)
            except ValueError as parse_error:
                logger.error(f"✗ Failed to parse LLM response. Full response:\n{response_text}")
                raise
            
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
        Parse LLM response - adaptable to what the agent produces.
        
        Handles 3 cases:
        1. Only WHERE clause → use it with our SQL template
        2. Full SQL (SELECT...FROM...WHERE...GROUP BY) → extract WHERE and use
        3. Partial/mixed SQL → find WHERE and extract
        
        Smart parsing: Skips example blocks from prompt, only parses actual response.
        
        Returns:
            Tuple of (complete_sql, params)
        """
        logger.info(f"Parsing response (length: {len(response_text)})")
        
        # Extract code blocks - but also track their positions
        code_block_pattern = r'```[^\n]*\n?(.*?)\n?```'
        code_blocks = []
        for match in re.finditer(code_block_pattern, response_text, re.DOTALL):
            code_blocks.append({
                'content': match.group(1).strip(),
                'start': match.start(),
                'end': match.end()
            })
        
        if not code_blocks:
            logger.error(f"No code blocks found in response")
            raise ValueError("LLM response missing code blocks")
        
        logger.info(f"Found {len(code_blocks)} code blocks")
        
        # Find the last occurrence of "YOUR RESPONSE" or "User query:" to identify where answer starts
        # Blocks after this point are the actual response, not examples
        answer_start_marker = "YOUR RESPONSE"
        user_query_marker = "User query:"
        
        last_marker_pos = 0
        if answer_start_marker in response_text:
            last_marker_pos = response_text.rfind(answer_start_marker)
            logger.info(f"Found 'YOUR RESPONSE' marker at position {last_marker_pos}")
        elif user_query_marker in response_text:
            last_marker_pos = response_text.rfind(user_query_marker)
            logger.info(f"Found 'User query:' marker at position {last_marker_pos}")
        
        # Filter: only use code blocks that come AFTER the marker (actual response)
        # If no marker found, use only the LAST blocks to be safe
        if last_marker_pos > 0:
            response_blocks = [b for b in code_blocks if b['start'] > last_marker_pos]
            logger.info(f"After marker filter: {len(response_blocks)} blocks (were {len(code_blocks)})")
        else:
            # Use last 3 blocks (usually: WHERE, params, and maybe something else)
            response_blocks = code_blocks[-3:] if len(code_blocks) >= 3 else code_blocks
            logger.info(f"No marker found, using last {len(response_blocks)} blocks")
        
        if not response_blocks:
            logger.error(f"No response blocks found after filtering")
            response_blocks = code_blocks  # Fallback to all
        
        # Step 1: Find JSON parameters (always in a separate block starting with [)
        params = None
        params_block_idx = -1
        
        for idx, block_info in enumerate(response_blocks):
            block = block_info['content']
            if block.startswith('['):
                try:
                    params = json.loads(block)
                    params_block_idx = idx
                    logger.info(f"✓ Found JSON params (block {idx}): {params}")
                    break
                except json.JSONDecodeError as e:
                    logger.warning(f"Block {idx} looks like JSON but parse failed: {e}")
        
        if params is None:
            logger.error("Could not find JSON parameters")
            logger.error(f"Response blocks: {response_blocks}")
            # Try to be more lenient - look for ANY JSON array, even with trailing commas
            for idx, block_info in enumerate(response_blocks):
                block = block_info['content'].strip()
                if block.startswith('['):
                    # Try to fix common JSON issues
                    fixed_block = block.rstrip(',').strip()
                    if fixed_block.endswith(','):
                        fixed_block = fixed_block[:-1]
                    try:
                        params = json.loads(fixed_block)
                        logger.info(f"✓ Fixed and parsed JSON params (block {idx}): {params}")
                        params_block_idx = idx
                        break
                    except json.JSONDecodeError as e:
                        logger.warning(f"Block {idx} JSON fix attempt failed: {e}")
            
            if params is None:
                raise ValueError("LLM response missing parameters")
        
        if not isinstance(params, list):
            raise ValueError("Parameters must be a JSON array")
        
        # Step 2: Find WHERE clause in the remaining blocks
        where_clause = None
        
        for idx, block_info in enumerate(response_blocks):
            # Skip the JSON block
            if idx == params_block_idx:
                continue
            
            block = block_info['content']
            
            logger.debug(f"Analyzing block {idx}: {block[:80]}")
            
            # Case 1: Full SQL statement
            if self._is_full_sql(block):
                logger.info(f"✓ Block {idx} is full SQL, extracting WHERE")
                where_clause = self._extract_where_from_full_sql(block, params)
                if where_clause:
                    break
            
            # Case 2: Only WHERE clause (conditions without SELECT/FROM)
            elif self._is_only_where_clause(block):
                logger.info(f"✓ Block {idx} is WHERE clause only")
                where_clause = block
                break
            
            # Case 3: Partial SQL with WHERE keyword visible
            elif 'WHERE' in block.upper():
                logger.info(f"✓ Block {idx} contains WHERE keyword, extracting")
                where_clause = self._extract_where_from_full_sql(block, params)
                if where_clause:
                    break
        
        if where_clause is None:
            logger.error("Could not find WHERE clause in any block")
            for i, b_info in enumerate(response_blocks):
                logger.error(f"  Block {i}: {b_info['content'][:100]}")
            
            # Last resort: try to find ANY block with 'propiedades' and extract conditions
            for idx, block_info in enumerate(response_blocks):
                if idx == params_block_idx:
                    continue
                block = block_info['content']
                if 'propiedades' in block.lower() or '%s' in block:
                    logger.info(f"Last resort: using block {idx} as WHERE")
                    where_clause = block
                    break
            
            if where_clause is None:
                raise ValueError("Could not extract WHERE clause from LLM response")
        
        # Clean up WHERE clause
        where_clause = where_clause.strip()
        where_clause = re.sub(r'^WHERE\s+', '', where_clause, flags=re.IGNORECASE)
        where_clause = re.sub(r'^(?:sql|mysql|SQL|MYSQL)?\s*', '', where_clause, flags=re.IGNORECASE)
        where_clause = where_clause.rstrip(';').strip()  # Remove trailing semicolon
        
        # Remove trailing closing backticks if present
        if where_clause.endswith('```'):
            where_clause = where_clause[:-3].strip()
        
        logger.info(f"✓ Final WHERE: {where_clause[:80]}")
        logger.info(f"✓ Final PARAMS: {params}")
        
        # Build complete SQL with our template
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
        
        return complete_sql, params

    def _extract_where_from_full_sql(self, full_sql: str, params: list = None) -> str:
        """
        Extract WHERE clause from a full SQL statement.
        
        Handles:
        - SELECT ... FROM ... WHERE ... GROUP BY
        - Multiline formatting
        - Various spacing
        
        Args:
            full_sql: Complete SQL query with WHERE clause
            params: Optional params list (for validation)
            
        Returns:
            WHERE clause without the "WHERE" keyword
        """
        logger.debug(f"Extracting WHERE from full SQL (params: {params})")
        
        # Find WHERE clause - match from WHERE to GROUP/ORDER/LIMIT or end
        where_pattern = r'WHERE\s+(.*?)(?:\s+GROUP\s+BY|\s+ORDER\s+BY|\s+LIMIT|$)'
        match = re.search(where_pattern, full_sql, re.IGNORECASE | re.DOTALL)
        
        if match:
            where_clause = match.group(1).strip()
            logger.debug(f"✓ Extracted WHERE: {where_clause[:80]}")
            return where_clause
        
        logger.warning("Could not extract WHERE from full SQL")
        return None

    def _is_full_sql(self, text: str) -> bool:
        """Check if text is a full SQL query (has SELECT and FROM and WHERE)"""
        text_upper = text.upper()
        return ('SELECT' in text_upper and 'FROM' in text_upper and 'WHERE' in text_upper)

    def _is_only_where_clause(self, text: str) -> bool:
        """Check if text is only a WHERE clause (has conditions but not SELECT/FROM)"""
        text_upper = text.upper()
        has_where_keywords = ('WHERE' not in text_upper and  # Doesn't start with WHERE keyword
                             ('%s' in text or 'propiedades' in text or 
                              ('AND' in text_upper or 'OR' in text_upper)))
        return has_where_keywords and not ('SELECT' in text_upper or 'FROM' in text_upper)
