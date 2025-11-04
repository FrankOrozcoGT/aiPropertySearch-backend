"""Search Property Use Case - Core business logic"""
from typing import Any

from app.domain.ports.llm_service import ILLMService
from app.domain.ports.property_repository import IPropertyRepository
from app.domain.schemas import SearchRequest, SearchResponse


class SearchPropertyUseCase:
    """
    SearchPropertyUseCase: Orchestrates searching for properties using natural language.
    
    Flow:
    1. Receive natural language query
    2. Generate SQL from query using LLM
    3. Validate SQL (security)
    4. Execute query in repository
    5. Return SQL + results
    
    Dependencies are injected (Hexagonal principle).
    Pure business logic - NO FastAPI, NO database details here.
    """

    def __init__(
        self,
        llm_service: ILLMService,
        property_repository: IPropertyRepository,
    ):
        """
        Initialize use case with required ports.
        
        Args:
            llm_service: LLM implementation (Ollama, OpenAI, etc.)
            property_repository: Repository implementation (MySQL, PostgreSQL, etc.)
        """
        self.llm_service = llm_service
        self.property_repository = property_repository

    async def execute(self, request: SearchRequest) -> SearchResponse:
        """
        Execute the search property use case.
        
        Args:
            request: SearchRequest with natural language query
            
        Returns:
            SearchResponse with generated SQL and results
            
        Raises:
            ValueError: If input validation fails
            RuntimeError: If LLM or database operations fail
        """
        # Step 1: Validate input
        if not request.query or not request.query.strip():
            raise ValueError("Query cannot be empty")

        # Step 2: Generate SQL from natural language using LLM
        sql = await self.llm_service.generate_sql(request.query)

        # Step 3: Validate SQL (security check - prevent SQL injection)
        is_valid = await self.llm_service.validate_sql(sql)
        if not is_valid:
            raise ValueError("Generated SQL failed validation - possible injection attack detected")

        # Step 4: Execute the query in the repository
        results = await self.property_repository.search(sql)

        # Step 5: Return formatted response
        return SearchResponse(sql=sql, results=results)
