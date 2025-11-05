"""Search Routes - HTTP endpoints for property search"""
import logging
from fastapi import APIRouter, HTTPException, status

from app.domain.schemas import SearchRequest, SearchResponse, ErrorResponse
from app.domain.use_cases.search_property import SearchPropertyUseCase

logger = logging.getLogger(__name__)


def create_search_router(use_case: SearchPropertyUseCase) -> APIRouter:
    """
    Factory function to create search router with injected dependencies.
    
    Args:
        use_case: SearchPropertyUseCase instance (dependency injection)
        
    Returns:
        APIRouter configured with search endpoints
    """
    router = APIRouter(prefix="/search", tags=["search"])

    @router.post(
        "",
        response_model=SearchResponse,
        responses={
            400: {"model": ErrorResponse, "description": "Invalid query"},
            500: {"model": ErrorResponse, "description": "Server error"},
        },
    )
    async def search_properties(request: SearchRequest) -> SearchResponse:
        """
        Search properties using natural language query.
        
        The query is translated to SQL via LLM, validated, and executed.
        
        Args:
            request: SearchRequest with natural language query
            
        Returns:
            SearchResponse with generated SQL and results
            
        Raises:
            HTTPException: If request validation or processing fails
        """
        try:
            logger.info(f"📝 Search request: {request.query[:50]}...")
            
            # Execute use case (contains all business logic)
            response = await use_case.execute(request)
            
            logger.info(f"✓ Search completed, returned {len(response.results)} results")
            return response
            
        except ValueError as e:
            logger.warning(f"⚠️  Validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
            
        except RuntimeError as e:
            logger.error(f"✗ Runtime error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to process search request. Check server logs.",
            )
            
        except Exception as e:
            logger.error(f"✗ Unexpected error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred",
            )

    return router
