"""
PRODUCTION SYSTEM INFRASTRUCTURE
Core infrastructure for a 9.9/10 production-grade platform.

Includes:
1. Observability (structured logging, tracing, metrics)
2. Circuit Breaker (prevent cascading failures)
3. Confidence Scoring (quality ratings on outputs)
4. Health Check & Self-Healing
5. Cost Control (resource tracking & limits)
"""

import asyncio
import json
import time
import os
import threading
import psutil
from typing import Dict, Optional, List, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque
from loguru import logger
import uuid


# ============================================================================
# 1. OBSERVABILITY STRATEGY
# ============================================================================

class StructuredLogger:
    """
    Structured JSON logging with request tracing.
    Every log has context: trace_id, component, timing.
    """
    
    LOG_FILE = "app/static/logs/urwa.jsonl"
    
    def __init__(self):
        os.makedirs(os.path.dirname(self.LOG_FILE), exist_ok=True)
        self.current_trace_id: Optional[str] = None
    
    def set_trace_id(self, trace_id: str = None) -> str:
        """Set trace ID for request correlation."""
        self.current_trace_id = trace_id or str(uuid.uuid4())[:8]
        return self.current_trace_id
    
    def log(self, level: str, message: str, component: str = "system",
            **extra_data):
        """Log structured JSON event."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.upper(),
            "trace_id": self.current_trace_id,
            "component": component,
            "message": message,
            **extra_data
        }
        
        # Write to file
        try:
            with open(self.LOG_FILE, 'a') as f:
                f.write(json.dumps(entry) + "\n")
        except:
            pass
        
        # Also log to console
        if level == "error":
            logger.error(f"[{component}] {message}")
        elif level == "warning":
            logger.warning(f"[{component}] {message}")
        else:
            logger.info(f"[{component}] {message}")
    
    def info(self, message: str, component: str = "system", **extra):
        self.log("info", message, component, **extra)
    
    def warning(self, message: str, component: str = "system", **extra):
        self.log("warning", message, component, **extra)
    
    def error(self, message: str, component: str = "system", **extra):
        self.log("error", message, component, **extra)
    
    def metric(self, name: str, value: float, unit: str = "", **labels):
        """Log a metric for dashboards."""
        self.log("metric", f"{name}={value}{unit}", "metrics",
                metric_name=name, metric_value=value, unit=unit, labels=labels)


class MetricsCollector:
    """
    Collect and expose metrics for monitoring.
    Prometheus-compatible format.
    """
    
    def __init__(self):
        self.counters: Dict[str, int] = defaultdict(int)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.start_time = datetime.now()
    
    def increment(self, name: str, value: int = 1, **labels):
        """Increment a counter."""
        key = self._make_key(name, labels)
        self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, **labels):
        """Set a gauge value."""
        key = self._make_key(name, labels)
        self.gauges[key] = value
    
    def observe(self, name: str, value: float, **labels):
        key = self._make_key(name, labels)
        self.histograms[key].append(value)
        # deque handles maxlen automatically
    
    def _make_key(self, name: str, labels: Dict) -> str:
        if labels:
            label_str = ",".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}}"
        return name
    
    def get_metrics(self) -> Dict:
        """Get all metrics in structured format."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        # Calculate histogram stats
        histogram_stats = {}
        for key, values in self.histograms.items():
            if values:
                sorted_vals = sorted(values)
                histogram_stats[key] = {
                    "count": len(values),
                    "sum": sum(values),
                    "avg": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "p50": sorted_vals[len(sorted_vals) // 2],
                    "p95": sorted_vals[int(len(sorted_vals) * 0.95)] if len(sorted_vals) > 1 else sorted_vals[0],
                    "p99": sorted_vals[int(len(sorted_vals) * 0.99)] if len(sorted_vals) > 1 else sorted_vals[0],
                }
        
        return {
            "uptime_seconds": uptime,
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": histogram_stats,
            "collected_at": datetime.now().isoformat()
        }
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format."""
        lines = []
        
        for key, value in self.counters.items():
            lines.append(f"urwa_{key} {value}")
        
        for key, value in self.gauges.items():
            lines.append(f"urwa_{key} {value}")
        
        return "\n".join(lines)


# ============================================================================
# 2. CIRCUIT BREAKER STRATEGY
# ============================================================================

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Blocked - too many failures
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreaker:
    """
    Prevents cascading failures by stopping requests to failing services.
    
    States:
    - CLOSED: Normal, requests pass through
    - OPEN: Blocked, fail fast for cooldown period  
    - HALF_OPEN: Testing with limited requests
    """
    
    name: str
    failure_threshold: int = 5       # Failures before opening
    recovery_timeout: int = 300      # Seconds before trying again
    half_open_max: int = 3           # Max requests in half-open state
    
    state: CircuitState = field(default=CircuitState.CLOSED)
    failure_count: int = field(default=0)
    success_count: int = field(default=0)
    last_failure_time: Optional[datetime] = field(default=None)
    half_open_count: int = field(default=0)
    
    def can_execute(self) -> bool:
        """Check if request can proceed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_count = 0
                    logger.info(f"[CircuitBreaker] {self.name}: OPEN → HALF_OPEN")
                    return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            # Allow limited requests
            if self.half_open_count < self.half_open_max:
                self.half_open_count += 1
                return True
            return False
        
        return False
    
    def record_success(self):
        """Record successful execution."""
        self.success_count += 1
        
        if self.state == CircuitState.HALF_OPEN:
            # Recovered! Close the circuit
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            logger.info(f"[CircuitBreaker] {self.name}: HALF_OPEN → CLOSED (recovered)")
    
    def record_failure(self):
        """Record failed execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            # Still failing, reopen
            self.state = CircuitState.OPEN
            logger.warning(f"[CircuitBreaker] {self.name}: HALF_OPEN → OPEN (still failing)")
        
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.warning(f"[CircuitBreaker] {self.name}: CLOSED → OPEN ({self.failure_count} failures)")
    
    def get_status(self) -> Dict:
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure": self.last_failure_time.isoformat() if self.last_failure_time else None
        }


class CircuitBreakerRegistry:
    """Manages circuit breakers for different domains/services."""
    
    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}
    
    def get_breaker(self, name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a service."""
        if name not in self.breakers:
            self.breakers[name] = CircuitBreaker(name=name)
        return self.breakers[name]
    
    def get_all_status(self) -> List[Dict]:
        return [b.get_status() for b in self.breakers.values()]
    
    def get_open_circuits(self) -> List[str]:
        """Get list of currently open (blocked) circuits."""
        return [
            name for name, breaker in self.breakers.items()
            if breaker.state == CircuitState.OPEN
        ]


# ============================================================================
# 3. CONFIDENCE SCORING STRATEGY
# ============================================================================

@dataclass
class ConfidenceScore:
    """
    Quality score for any output.
    Makes results explainable and defensible.
    """
    
    overall: float = 0.0           # 0.0 to 1.0
    source_count: int = 0          # Number of sources
    extraction_quality: str = ""   # low/medium/high
    freshness: str = ""            # fresh/recent/stale
    consistency: float = 0.0       # How consistent across sources
    coverage: float = 0.0          # How much of query was answered
    
    factors: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ConfidenceCalculator:
    """
    Calculate confidence scores for scraping/analysis results.
    """
    
    @classmethod
    def calculate(cls, 
                  content: str = "",
                  sources: List[str] = None,
                  extraction_method: str = "",
                  response_time: float = 0,
                  status_code: int = 200,
                  has_structured_data: bool = False) -> ConfidenceScore:
        """
        Calculate confidence score for a result.
        """
        score = ConfidenceScore()
        sources = sources or []
        
        # Factor: Content length
        if len(content) > 5000:
            score.factors["content_length"] = 1.0
        elif len(content) > 1000:
            score.factors["content_length"] = 0.7
        elif len(content) > 100:
            score.factors["content_length"] = 0.4
        else:
            score.factors["content_length"] = 0.1
            score.warnings.append("Very short content")
        
        # Factor: Source count
        score.source_count = len(sources)
        if score.source_count >= 5:
            score.factors["source_count"] = 1.0
        elif score.source_count >= 3:
            score.factors["source_count"] = 0.7
        elif score.source_count >= 1:
            score.factors["source_count"] = 0.4
        else:
            score.factors["source_count"] = 0.1
            score.warnings.append("No source attribution")
        
        # Factor: Extraction method
        extraction_scores = {
            "structured": 1.0,
            "semantic": 0.8,
            "generic": 0.6,
            "fallback": 0.4,
            "raw": 0.2
        }
        score.factors["extraction"] = extraction_scores.get(extraction_method, 0.5)
        
        # Factor: Response quality
        if status_code == 200:
            score.factors["response"] = 1.0
        elif status_code in [301, 302]:
            score.factors["response"] = 0.8
        else:
            score.factors["response"] = 0.3
            score.warnings.append(f"Non-200 status: {status_code}")
        
        # Factor: Structured data
        if has_structured_data:
            score.factors["structured_data"] = 1.0
        else:
            score.factors["structured_data"] = 0.5
        
        # Factor: Response time (faster = more likely successful)
        if response_time < 2:
            score.factors["speed"] = 1.0
        elif response_time < 5:
            score.factors["speed"] = 0.8
        elif response_time < 10:
            score.factors["speed"] = 0.6
        else:
            score.factors["speed"] = 0.4
            score.warnings.append("Slow response")
        
        # Calculate overall score (weighted average)
        weights = {
            "content_length": 0.25,
            "source_count": 0.20,
            "extraction": 0.20,
            "response": 0.15,
            "structured_data": 0.10,
            "speed": 0.10
        }
        
        total = sum(score.factors.get(k, 0) * w for k, w in weights.items())
        score.overall = round(total, 2)
        
        # Set quality level
        if score.overall >= 0.8:
            score.extraction_quality = "high"
        elif score.overall >= 0.5:
            score.extraction_quality = "medium"
        else:
            score.extraction_quality = "low"
        
        return score


# ============================================================================
# 4. HEALTH CHECK & SELF-HEALING STRATEGY
# ============================================================================

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ComponentHealth:
    name: str
    status: HealthStatus
    message: str = ""
    last_check: datetime = field(default_factory=datetime.now)
    metrics: Dict = field(default_factory=dict)


class HealthChecker:
    """
    Monitor system health and trigger self-healing.
    """
    
    def __init__(self):
        self.components: Dict[str, ComponentHealth] = {}
        self.recovery_actions: Dict[str, Callable] = {}
        self.check_interval = 60  # seconds
        self._running = False
    
    def register_component(self, name: str, 
                          check_func: Callable[[], bool],
                          recovery_func: Callable[[], bool] = None):
        """Register a component for health monitoring."""
        self.components[name] = ComponentHealth(
            name=name,
            status=HealthStatus.HEALTHY
        )
        
        if recovery_func:
            self.recovery_actions[name] = recovery_func
    
    async def check_all(self) -> Dict[str, ComponentHealth]:
        """Check health of all components."""
        results = {}
        
        # Check system resources
        # Use interval=1 to get accurate CPU reading (first call with interval=None returns 0)
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # System health
        system_status = HealthStatus.HEALTHY
        system_message = "All systems operational"
        
        if cpu_percent > 90:
            system_status = HealthStatus.DEGRADED
            system_message = f"High CPU: {cpu_percent:.1f}%"
        
        if memory.percent > 90:
            system_status = HealthStatus.DEGRADED
            system_message = f"High memory: {memory.percent:.1f}%"
        
        if disk.percent > 95:
            system_status = HealthStatus.UNHEALTHY
            system_message = f"Disk almost full: {disk.percent:.1f}%"
        
        results["system"] = ComponentHealth(
            name="system",
            status=system_status,
            message=system_message,
            metrics={
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "disk_percent": round(disk.percent, 1)
            }
        )
        
        # Check Playwright availability
        try:
            from playwright.sync_api import sync_playwright
            results["playwright"] = ComponentHealth(
                name="playwright",
                status=HealthStatus.HEALTHY,
                message="Playwright available"
            )
        except Exception as e:
            results["playwright"] = ComponentHealth(
                name="playwright",
                status=HealthStatus.UNHEALTHY,
                message=f"Playwright error: {str(e)}"
            )
        
        return results
    
    async def self_heal(self, component: str) -> bool:
        """Attempt to recover a failing component."""
        if component not in self.recovery_actions:
            logger.warning(f"[Health] No recovery action for {component}")
            return False
        
        try:
            logger.info(f"[Health] Attempting recovery for {component}")
            success = self.recovery_actions[component]()
            
            if success:
                logger.info(f"[Health] Recovery successful for {component}")
                self.components[component].status = HealthStatus.HEALTHY
            else:
                logger.error(f"[Health] Recovery failed for {component}")
            
            return success
        except Exception as e:
            logger.error(f"[Health] Recovery error for {component}: {e}")
            return False
    
    def get_overall_status(self) -> Dict:
        """Get overall system health status."""
        statuses = [c.status for c in self.components.values()]
        
        if all(s == HealthStatus.HEALTHY for s in statuses):
            overall = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in statuses):
            overall = HealthStatus.UNHEALTHY
        else:
            overall = HealthStatus.DEGRADED
        
        return {
            "status": overall.value,
            "components": {
                name: {
                    "status": c.status.value,
                    "message": c.message,
                    "last_check": c.last_check.isoformat(),
                    "metrics": c.metrics
                }
                for name, c in self.components.items()
            },
            "checked_at": datetime.now().isoformat()
        }


# ============================================================================
# 5. COST CONTROL STRATEGY
# ============================================================================

@dataclass
class ResourceUsage:
    """Track resource consumption."""
    
    # Compute
    cpu_seconds: float = 0
    browser_time: float = 0
    
    # External services
    llm_tokens: int = 0
    llm_requests: int = 0
    search_requests: int = 0
    
    # Network
    bytes_downloaded: int = 0
    proxy_requests: int = 0
    
    # Storage
    cache_size_bytes: int = 0
    evidence_size_bytes: int = 0
    
    # Costs (estimated)
    estimated_cost_usd: float = 0


class CostController:
    """
    Track and limit resource usage.
    Prevents runaway costs.
    """
    
    # Cost estimates (configurable)
    COSTS = {
        "llm_token": 0.00001,        # $0.01 per 1000 tokens
        "browser_minute": 0.001,      # $0.001 per minute
        "proxy_request": 0.0001,      # $0.0001 per request
        "search_request": 0.001,      # $0.001 per search
    }
    
    # Default limits
    DEFAULT_LIMITS = {
        "llm_tokens_per_hour": 100000,
        "browser_minutes_per_hour": 60,
        "requests_per_hour": 1000,
        "cost_per_hour_usd": 1.0,
    }
    
    def __init__(self):
        self.usage: Dict[str, ResourceUsage] = defaultdict(ResourceUsage)
        self.hourly_usage: Dict[str, ResourceUsage] = defaultdict(ResourceUsage)
        self.limits = self.DEFAULT_LIMITS.copy()
        self.last_reset = datetime.now()
    
    def _get_current_hour_key(self) -> str:
        return datetime.now().strftime("%Y-%m-%d-%H")
    
    def _maybe_reset_hourly(self):
        """Reset hourly counters if new hour and purge old data."""
        hour_key = self._get_current_hour_key()
        
        # Purge data older than 24 hours to prevent memory leak
        try:
            current_dt = datetime.datetime.now()
            cutoff = (current_dt - datetime.timedelta(hours=24)).strftime("%Y-%m-%d-%H")
            
            keys_to_delete = [k for k in self.hourly_usage if k < cutoff]
            for k in keys_to_delete:
                del self.hourly_usage[k]
        except Exception:
            pass
        
        if hour_key not in self.hourly_usage:
            # New hour, initialize
            self.hourly_usage[hour_key] = ResourceUsage()
    
    def track_llm(self, tokens: int, user_id: str = "default"):
        """Track LLM token usage."""
        self._maybe_reset_hourly()
        
        hour_key = self._get_current_hour_key()
        self.hourly_usage[hour_key].llm_tokens += tokens
        self.hourly_usage[hour_key].llm_requests += 1
        self.usage[user_id].llm_tokens += tokens
        
        # Update cost
        cost = tokens * self.COSTS["llm_token"]
        self.hourly_usage[hour_key].estimated_cost_usd += cost
        self.usage[user_id].estimated_cost_usd += cost
    
    def track_browser(self, seconds: float, user_id: str = "default"):
        """Track browser usage time."""
        hour_key = self._get_current_hour_key()
        minutes = seconds / 60
        
        self.hourly_usage[hour_key].browser_time += seconds
        self.usage[user_id].browser_time += seconds
        
        cost = minutes * self.COSTS["browser_minute"]
        self.hourly_usage[hour_key].estimated_cost_usd += cost
    
    def track_proxy(self, user_id: str = "default"):
        """Track proxy request."""
        hour_key = self._get_current_hour_key()
        
        self.hourly_usage[hour_key].proxy_requests += 1
        self.usage[user_id].proxy_requests += 1
        
        self.hourly_usage[hour_key].estimated_cost_usd += self.COSTS["proxy_request"]
    
    def track_search(self, user_id: str = "default"):
        """Track search API request."""
        hour_key = self._get_current_hour_key()
        
        self.hourly_usage[hour_key].search_requests += 1
        self.usage[user_id].search_requests += 1
        
        self.hourly_usage[hour_key].estimated_cost_usd += self.COSTS["search_request"]
    
    def track_download(self, bytes_count: int, user_id: str = "default"):
        """Track downloaded bytes."""
        self.usage[user_id].bytes_downloaded += bytes_count
    
    def check_limits(self, user_id: str = "default") -> Dict[str, bool]:
        """Check if any limits are exceeded."""
        hour_key = self._get_current_hour_key()
        hourly = self.hourly_usage.get(hour_key, ResourceUsage())
        
        return {
            "llm_exceeded": hourly.llm_tokens > self.limits["llm_tokens_per_hour"],
            "browser_exceeded": (hourly.browser_time / 60) > self.limits["browser_minutes_per_hour"],
            "cost_exceeded": hourly.estimated_cost_usd > self.limits["cost_per_hour_usd"],
            "any_exceeded": any([
                hourly.llm_tokens > self.limits["llm_tokens_per_hour"],
                (hourly.browser_time / 60) > self.limits["browser_minutes_per_hour"],
                hourly.estimated_cost_usd > self.limits["cost_per_hour_usd"]
            ])
        }
    
    def get_usage_stats(self, user_id: str = "default") -> Dict:
        """Get usage statistics."""
        hour_key = self._get_current_hour_key()
        hourly = self.hourly_usage.get(hour_key, ResourceUsage())
        total = self.usage.get(user_id, ResourceUsage())
        
        return {
            "current_hour": {
                "llm_tokens": hourly.llm_tokens,
                "llm_requests": hourly.llm_requests,
                "browser_minutes": round(hourly.browser_time / 60, 2),
                "search_requests": hourly.search_requests,
                "proxy_requests": hourly.proxy_requests,
                "estimated_cost_usd": round(hourly.estimated_cost_usd, 4)
            },
            "total": {
                "llm_tokens": total.llm_tokens,
                "browser_minutes": round(total.browser_time / 60, 2),
                "bytes_downloaded": total.bytes_downloaded,
                "estimated_cost_usd": round(total.estimated_cost_usd, 4)
            },
            "limits": self.limits,
            "limits_status": self.check_limits(user_id)
        }
    
    def set_limit(self, limit_name: str, value: float):
        """Update a limit."""
        if limit_name in self.limits:
            self.limits[limit_name] = value


# ============================================================================
# SINGLETON INSTANCES
# ============================================================================

structured_logger = StructuredLogger()
metrics_collector = MetricsCollector()
circuit_breakers = CircuitBreakerRegistry()
confidence_calculator = ConfidenceCalculator()
health_checker = HealthChecker()
cost_controller = CostController()


# ============================================================================
# HELPER DECORATORS
# ============================================================================

def with_circuit_breaker(domain: str):
    """Decorator to wrap function with circuit breaker."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            breaker = circuit_breakers.get_breaker(domain)
            
            if not breaker.can_execute():
                raise Exception(f"Circuit open for {domain} - request blocked")
            
            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure()
                raise
        
        return wrapper
    return decorator


def with_cost_tracking(resource_type: str):
    """Decorator to track resource usage."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            result = await func(*args, **kwargs)
            
            elapsed = time.time() - start_time
            
            if resource_type == "browser":
                cost_controller.track_browser(elapsed)
            elif resource_type == "search":
                cost_controller.track_search()
            
            return result
        
        return wrapper
    return decorator


def with_metrics(operation_name: str):
    """Decorator to collect metrics for an operation."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            
            try:
                result = await func(*args, **kwargs)
                success = True
                return result
            finally:
                elapsed = time.time() - start_time
                
                metrics_collector.increment(
                    f"{operation_name}_total",
                    status="success" if success else "error"
                )
                metrics_collector.observe(
                    f"{operation_name}_duration_seconds",
                    elapsed
                )
        
        return wrapper
    return decorator
