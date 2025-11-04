"""Domain Schemas - Request/Response models for search functionality"""
from pydantic import BaseModel, Field
from typing import Any


class SearchRequest(BaseModel):
    """Request to search properties using natural language"""
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Natural language search query (e.g., 'casas de 3 habitaciones en zona 10')"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Busco casas de 3 habitaciones en zona 10"
            }
        }


class SearchResponse(BaseModel):
    """Response with generated SQL and search results"""
    sql: str = Field(
        ...,
        description="Generated SQL query"
    )
    results: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of property records matching the search"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "sql": "SELECT * FROM propiedades WHERE habitaciones = 3 AND ubicacion LIKE '%zona 10%'",
                "results": [
                    {
                        "id": 1,
                        "titulo": "Casa moderna",
                        "precio": 250000,
                        "habitaciones": 3
                    }
                ]
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    detail: str = Field(
        ...,
        description="Error message"
    )
    error_code: str | None = Field(
        default=None,
        description="Machine-readable error code"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Failed to connect to LLM service",
                "error_code": "LLM_CONNECTION_ERROR"
            }
        }
