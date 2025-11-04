"""Dependency Injection - Container and factory for creating use cases with dependencies"""
import logging

from app.domain.use_cases.search_property import SearchPropertyUseCase
from app.domain.ports.property_repository import IPropertyRepository
from app.domain.ports.llm_service import ILLMService

logger = logging.getLogger(__name__)


class ServiceContainer:
    """
    Service container for managing application dependencies.
    
    Implements the service locator pattern to provide instances
    of use cases with their dependencies properly injected.
    """

    def __init__(
        self,
        property_repository: IPropertyRepository,
        llm_service: ILLMService,
    ):
        """
        Initialize service container with adapters.
        
        Args:
            property_repository: Implementation of IPropertyRepository
            llm_service: Implementation of ILLMService
        """
        self._property_repository = property_repository
        self._llm_service = llm_service

    def get_search_property_use_case(self) -> SearchPropertyUseCase:
        """
        Get SearchPropertyUseCase with all dependencies injected.
        
        Returns:
            Configured SearchPropertyUseCase instance
        """
        logger.debug("Creating SearchPropertyUseCase instance")
        
        return SearchPropertyUseCase(
            llm_service=self._llm_service,
            property_repository=self._property_repository,
        )

    # Future use cases can be added here as the app grows
    # def get_another_use_case(self) -> AnotherUseCase:
    #     return AnotherUseCase(...)
