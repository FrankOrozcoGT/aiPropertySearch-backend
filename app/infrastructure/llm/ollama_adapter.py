"""Ollama LLM Adapter - Integration with Ollama for SQL generation"""
import logging
import re
from typing import Optional

import requests

from app.config import settings
from app.domain.ports.llm_service import ILLMService

logger = logging.getLogger(__name__)


class OllamaLLMAdapter(ILLMService):
    """
    LLM adapter for Ollama.
    
    Implements ILLMService port.
    Uses Ollama to generate SQL from natural language queries.
    """

    # SQL validation patterns
    FORBIDDEN_KEYWORDS = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE",
        "TRUNCATE", "EXEC", "EXECUTE", "SCRIPT", "PRAGMA"
    ]
    ALLOWED_KEYWORDS = ["SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER", "ON", "AND", "OR", "LIKE", "IN", "BETWEEN", "ORDER", "BY", "LIMIT", "GROUP", "HAVING", "DISTINCT"]

    def __init__(self, timeout: int = 30):
        """
        Initialize Ollama adapter.
        
        Args:
            timeout: Request timeout in seconds (default: 30)
        """
        self.base_url = settings.OLLAMA_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = timeout
        
        logger.info(f"✓ Ollama adapter initialized: {self.base_url} (model: {self.model})")

    async def generate_sql(self, query: str) -> str:
        """
        Generate SQL from natural language query using Ollama.
        
        Args:
            query: Natural language search query
            
        Returns:
            Generated SQL query
            
        Raises:
            ValueError: If query is empty
            RuntimeError: If Ollama connection fails or times out
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        logger.info(f"📝 Generating SQL for query: {query[:50]}...")

        # Build the prompt
        prompt = self._build_prompt(query)

        try:
            # Call Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=self.timeout,
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Ollama API error: {response.status_code} - {response.text}"
                )

            result = response.json()
            sql_query = result.get("response", "").strip()

            if not sql_query:
                raise RuntimeError("Ollama returned empty response")

            logger.info(f"✓ SQL generated successfully: {sql_query[:100]}...")

            return sql_query

        except requests.Timeout:
            logger.error(f"✗ Ollama request timeout (>{self.timeout}s)")
            raise RuntimeError(
                f"LLM request timed out after {self.timeout} seconds"
            )

        except requests.ConnectionError as e:
            logger.error(f"✗ Ollama connection error: {str(e)}")
            raise RuntimeError(
                f"Failed to connect to Ollama at {self.base_url}: {str(e)}"
            )

        except Exception as e:
            logger.error(f"✗ Ollama error: {str(e)}")
            raise RuntimeError(f"Failed to generate SQL: {str(e)}")

    async def validate_sql(self, sql: str) -> bool:
        """
        Validate if SQL is safe to execute.
        
        Checks:
        - Only SELECT statements allowed
        - No forbidden keywords (DROP, DELETE, etc.)
        - No SQL injection patterns
        
        Args:
            sql: SQL query to validate
            
        Returns:
            True if SQL is valid and safe
            
        Raises:
            ValueError: If SQL is dangerous or invalid
        """
        try:
            sql_upper = sql.upper().strip()

            # Check 1: Must start with SELECT
            if not sql_upper.startswith("SELECT"):
                raise ValueError("Only SELECT queries are allowed")

            # Check 2: No forbidden keywords
            for keyword in self.FORBIDDEN_KEYWORDS:
                if keyword in sql_upper:
                    raise ValueError(
                        f"Forbidden SQL keyword detected: {keyword}"
                    )

            # Check 3: No semicolon at the end
            if sql.strip().endswith(";"):
                raise ValueError("SQL query should not end with semicolon")

            # Check 4: No multiple statements
            if ";" in sql.strip():
                raise ValueError("Multiple SQL statements not allowed")

            # Check 5: Basic SQL injection patterns
            dangerous_patterns = [
                r"--\s*$",  # SQL comment at end
                r"/\*.*\*/",  # Block comments
                r"xp_",  # Extended stored procedures
                r"sp_",  # System stored procedures
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, sql_upper):
                    raise ValueError(f"Dangerous SQL pattern detected: {pattern}")

            logger.info(f"✓ SQL validation passed: {sql[:100]}...")
            return True

        except ValueError as e:
            logger.warning(f"⚠️ SQL validation failed: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"✗ Validation error: {str(e)}")
            raise RuntimeError(f"SQL validation error: {str(e)}")

    def _build_prompt(self, query: str) -> str:
        """
        Build the prompt for Ollama.
        
        Args:
            query: Natural language query
            
        Returns:
            Formatted prompt for LLM
        """
        prompt = f"""You are an SQL expert assistant. Your task is to translate natural language queries into SQL.

Database Schema:
- propiedades: id, titulo, descripcion, tipo, precio, habitaciones, banos, area_m2, ubicacion, zona_administrativa, fecha_publicacion, estado
- amenidades: id, nombre, tipo, ubicacion, zona_administrativa
- propiedades_amenidades: id, propiedad_id, amenidad_id, distancia_km, notas

Property types available: casa, departamento, terreno, local, oficina
Amenity types: colegio, parada_bus, supermercado, parque, hospital, gym, restaurante, cine, banco, farmacia, centroComercial

Rules:
1. Generate ONLY a valid MySQL SELECT query
2. NO explanations, NO comments, ONLY the SQL
3. NO semicolon at the end
4. Use only SELECT statements
5. Join tables if needed for amenity queries
6. Filter by estado = 'activa' when searching for available properties
7. Use LIKE for text searches

User query: {query}

Generate the SQL query:"""

        return prompt
