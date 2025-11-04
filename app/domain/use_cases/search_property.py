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
    2. Generate SQL + PARAMS from query using LLM (separated for security)
    3. Validate SQL template structure
    4. Execute query with parameterized values (100% SQL injection proof)
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

        # Step 2: Generate SQL + PARAMS from natural language using LLM
        sql_template, params = await self.llm_service.generate_sql_with_params(
            request.query
        )

        # Step 3: Validate SQL template (with params separated)
        is_valid = await self.llm_service.validate_sql_template(sql_template, params)
        if not is_valid:
            raise ValueError("Generated SQL template failed validation")

        # Step 4: Execute the parameterized query in the repository (100% safe)
        results = await self.property_repository.search(sql_template, params)

        # Step 5: Return formatted response
        return SearchResponse(sql=sql_template, results=results)
