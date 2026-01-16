"""
URWA Core Production Infrastructure

This module contains the production-grade infrastructure:
- Observability (structured logging, metrics)
- Circuit Breaker (prevent cascading failures)
- Confidence Scoring (quality ratings)
- Health Check & Self-Healing
- Cost Control (resource tracking)
- Data Quality (normalization, versioned extractors)
"""

from .production_infra import (
    # Observability
    StructuredLogger,
    structured_logger,
    MetricsCollector,
    metrics_collector,
    
    # Circuit Breaker
    CircuitBreaker,
    CircuitBreakerRegistry,
    circuit_breakers,
    CircuitState,
    
    # Confidence Scoring
    ConfidenceScore,
    ConfidenceCalculator,
    confidence_calculator,
    
    # Health Check
    HealthChecker,
    health_checker,
    HealthStatus,
    ComponentHealth,
    
    # Cost Control
    CostController,
    cost_controller,
    ResourceUsage,
    
    # Decorators
    with_circuit_breaker,
    with_cost_tracking,
    with_metrics,
)

from .data_quality import (
    # Normalization
    DataNormalizer,
    data_normalizer,
    
    # Versioned Extractors
    VersionedExtractor,
    ExtractorRegistry,
    extractor_registry,
    ExtractorVersion,
)

__all__ = [
    # Observability
    'StructuredLogger',
    'structured_logger',
    'MetricsCollector',
    'metrics_collector',
    
    # Circuit Breaker
    'CircuitBreaker',
    'CircuitBreakerRegistry',
    'circuit_breakers',
    'CircuitState',
    
    # Confidence Scoring
    'ConfidenceScore',
    'ConfidenceCalculator',
    'confidence_calculator',
    
    # Health Check
    'HealthChecker',
    'health_checker',
    'HealthStatus',
    'ComponentHealth',
    
    # Cost Control
    'CostController',
    'cost_controller',
    'ResourceUsage',
    
    # Data Quality
    'DataNormalizer',
    'data_normalizer',
    'VersionedExtractor',
    'ExtractorRegistry',
    'extractor_registry',
    'ExtractorVersion',
    
    # Decorators
    'with_circuit_breaker',
    'with_cost_tracking',
    'with_metrics',
]
