"""Ollama LLM Adapter - Integration with Ollama for SQL generation"""
import json
import logging
from typing import Tuple

import requests
import sqlglot
from sqlglot import exp

from app.config import settings
from app.domain.ports.llm_service import ILLMService

logger = logging.getLogger(__name__)


class OllamaLLMAdapter(ILLMService):
    """
    LLM adapter for Ollama.
    
    Implements ILLMService port.
    Uses Ollama to generate SQL with separated parameters from natural language queries.
    Uses sqlglot for validation (professional SQL parser used by Meta, Stripe, etc.)
    """

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

        # System prompt tells IA to return JSON with sql + params
        system_prompt = """You are a SQL expert. Generate SAFE SQL queries with parameterized queries.

IMPORTANT RULES:
1. Always return ONLY valid JSON (no other text) with TWO fields:
   - "sql": SQL query with ? placeholders instead of values
   - "params": Array of values in order

EXAMPLE 1:
Query: "casas baratas en zona 10"
Response:
{
  "sql": "SELECT * FROM propiedades WHERE precio < ? AND zona_administrativa = ?",
  "params": [500000, "zona 10"]
}

EXAMPLE 2:
Query: "departamentos con 3 habitaciones"
Response:
{
  "sql": "SELECT * FROM propiedades WHERE tipo = ? AND habitaciones = ?",
  "params": ["departamento", 3]
}

Database Schema:
- propiedades: id, titulo, descripcion, tipo, precio, habitaciones, banos, area_m2, ubicacion, zona_administrativa, fecha_publicacion, estado
- amenidades: id, nombre, tipo, ubicacion, zona_administrativa
- propiedades_amenidades: id, propiedad_id, amenidad_id, distancia_km, notas

Property types: casa, departamento, terreno, local, oficina
Amenity types: colegio, parada_bus, supermercado, parque, hospital, gym, restaurante, cine, banco, farmacia, centroComercial

RULES:
- Use ? for each parameter (MySQL style)
- First ? = first param in array
- Never put literal values in SQL string
- Only SELECT queries allowed
- Always return valid JSON only
- Parameters should be typed correctly (numbers as numbers, text as strings)
- Filter by estado = 'activa' when searching available properties
"""

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
            logger.debug(f"Ollama response: {response_text[:100]}...")
            
            # Parse JSON response
            try:
                parsed = json.loads(response_text)
            except json.JSONDecodeError:
                logger.error(f"LLM returned invalid JSON: {response_text}")
                raise ValueError("LLM did not return valid JSON format")
            
            # Extract sql and params
            if "sql" not in parsed or "params" not in parsed:
                logger.error(f"LLM JSON missing required fields: {parsed}")
                raise ValueError("LLM response missing 'sql' or 'params' field")
            
            sql = parsed["sql"].strip()
            params = parsed.get("params", [])
            
            if not isinstance(params, list):
                raise ValueError("'params' field must be an array")
            
            logger.info(f"✓ Generated SQL template with {len(params)} parameters")
            
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
        Validate if SQL template is safe to execute using sqlglot.
        
        Args:
            sql: SQL template with ? placeholders (no literal values)
            params: Array of parameter values
            
        Returns:
            True if SQL is valid and safe
            
        Raises:
            ValueError: If SQL is invalid or dangerous
        """
        try:
            logger.debug(f"Validating SQL template: {sql[:50]}...")
            
            # Check 1: Count placeholders matches params
            placeholder_count = sql.count("?")
            if placeholder_count != len(params):
                raise ValueError(
                    f"SQL has {placeholder_count} placeholders but {len(params)} params provided"
                )
            
            # Check 2: Use sqlglot to parse and validate SQL structure
            try:
                parsed = sqlglot.parse_one(sql)
            except sqlglot.ParseError as e:
                logger.error(f"SQL syntax error: {str(e)}")
                raise ValueError(f"Invalid SQL syntax: {str(e)}")
            
            # Check 3: Must be SELECT query only
            if not isinstance(parsed, exp.Select):
                raise ValueError("Only SELECT queries are allowed")
            
            # Check 4: Check for dangerous keywords in the AST
            # (sqlglot parses structure, so we check the expression type)
            dangerous_types = (
                exp.Drop, exp.Delete, exp.Update, exp.Insert,
                exp.Alter, exp.Create, exp.Truncate
            )
            
            for node in parsed.walk():
                if isinstance(node, dangerous_types):
                    raise ValueError(f"Forbidden operation: {type(node).__name__}")
            
            # Check 5: No comment-based injection patterns
            if "--" in sql or "/*" in sql or "*/" in sql:
                raise ValueError("Comment-based SQL injection patterns detected")
            
            # Check 6: No semicolon (indicates multiple statements)
            if ";" in sql:
                raise ValueError("Multiple SQL statements not allowed")
            
            logger.info("✓ SQL template validation passed (sqlglot)")
            return True
            
        except ValueError as e:
            logger.warning(f"⚠️ SQL validation failed: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"✗ Unexpected validation error: {str(e)}", exc_info=True)
            raise ValueError(f"SQL validation failed: {str(e)}")
