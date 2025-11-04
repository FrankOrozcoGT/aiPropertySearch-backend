"""Ports - Abstractions/Contracts for external services"""
from .property_repository import IPropertyRepository
from .llm_service import ILLMService

__all__ = ["IPropertyRepository", "ILLMService"]
