"""
Monitoring and Metrics Module for Voice Agent Demo
Provides health checks, metrics, and performance monitoring
"""

from fastapi import APIRouter
from datetime import datetime, timedelta
from typing import Dict, List
import psutil
import time

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])

# In-memory metrics storage (use Redis/database for production)
metrics_store = {
    "requests": [],
    "errors": [],
    "latencies": [],
    "cache_hits": 0,
    "cache_misses": 0,
    "start_time": datetime.now()
}

class MetricsCollector:
    """Collect and store application metrics"""
    
    @staticmethod
    def record_request(endpoint: str, duration_ms: float, status_code: int):
        """Record API request metrics"""
        metrics_store["requests"].append({
            "endpoint": endpoint,
            "duration_ms": duration_ms,
            "status_code": status_code,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 1000 requests
        if len(metrics_store["requests"]) > 1000:
            metrics_store["requests"] = metrics_store["requests"][-1000:]
    
    @staticmethod
    def record_error(endpoint: str, error_type: str, error_message: str):
        """Record application errors"""
        metrics_store["errors"].append({
            "endpoint": endpoint,
            "error_type": error_type,
            "error_message": error_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 500 errors
        if len(metrics_store["errors"]) > 500:
            metrics_store["errors"] = metrics_store["errors"][-500:]
    
    @staticmethod
    def record_latency(component: str, duration_ms: float):
        """Record component latency"""
        metrics_store["latencies"].append({
            "component": component,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 1000 latencies
        if len(metrics_store["latencies"]) > 1000:
            metrics_store["latencies"] = metrics_store["latencies"][-1000:]
    
    @staticmethod
    def record_cache_hit():
        """Record cache hit"""
        metrics_store["cache_hits"] += 1
    
    @staticmethod
    def record_cache_miss():
        """Record cache miss"""
        metrics_store["cache_misses"] += 1


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint
    Returns system health, uptime, and basic metrics
    """
    uptime = datetime.now() - metrics_store["start_time"]
    
    # System metrics
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Calculate error rate
    total_requests = len(metrics_store["requests"])
    error_count = len(metrics_store["errors"])
    error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
    
    # Calculate average latency
    recent_requests = metrics_store["requests"][-100:]  # Last 100 requests
    avg_latency = sum(r["duration_ms"] for r in recent_requests) / len(recent_requests) if recent_requests else 0
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": uptime.total_seconds(),
        "uptime_formatted": str(uptime),
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_mb": memory.available / (1024 * 1024),
            "disk_percent": disk.percent,
            "disk_free_gb": disk.free / (1024 * 1024 * 1024)
        },
        "metrics": {
            "total_requests": total_requests,
            "total_errors": error_count,
            "error_rate_percent": round(error_rate, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "cache_hit_rate": calculate_cache_hit_rate()
        }
    }


@router.get("/metrics")
async def get_metrics():
    """
    Get detailed application metrics
    """
    # Calculate metrics for last hour
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    recent_requests = [
        r for r in metrics_store["requests"]
        if datetime.fromisoformat(r["timestamp"]) > one_hour_ago
    ]
    
    recent_errors = [
        e for e in metrics_store["errors"]
        if datetime.fromisoformat(e["timestamp"]) > one_hour_ago
    ]
    
    # Endpoint breakdown
    endpoint_stats = {}
    for req in recent_requests:
        endpoint = req["endpoint"]
        if endpoint not in endpoint_stats:
            endpoint_stats[endpoint] = {
                "count": 0,
                "total_duration": 0,
                "errors": 0
            }
        endpoint_stats[endpoint]["count"] += 1
        endpoint_stats[endpoint]["total_duration"] += req["duration_ms"]
    
    # Calculate averages
    for endpoint, stats in endpoint_stats.items():
        stats["avg_duration_ms"] = round(stats["total_duration"] / stats["count"], 2)
        del stats["total_duration"]
    
    # Component latency breakdown
    component_latencies = {}
    for latency in metrics_store["latencies"][-100:]:
        component = latency["component"]
        if component not in component_latencies:
            component_latencies[component] = []
        component_latencies[component].append(latency["duration_ms"])
    
    component_stats = {}
    for component, latencies in component_latencies.items():
        component_stats[component] = {
            "avg_ms": round(sum(latencies) / len(latencies), 2),
            "min_ms": round(min(latencies), 2),
            "max_ms": round(max(latencies), 2),
            "count": len(latencies)
        }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "time_window": "last_1_hour",
        "summary": {
            "total_requests": len(recent_requests),
            "total_errors": len(recent_errors),
            "error_rate_percent": round(len(recent_errors) / len(recent_requests) * 100, 2) if recent_requests else 0,
            "cache_hit_rate_percent": calculate_cache_hit_rate()
        },
        "endpoints": endpoint_stats,
        "components": component_stats,
        "recent_errors": recent_errors[-10:]  # Last 10 errors
    }


@router.get("/performance")
async def get_performance_metrics():
    """
    Get performance metrics and latency breakdown
    """
    recent_latencies = metrics_store["latencies"][-100:]
    
    # Group by component
    by_component = {}
    for item in recent_latencies:
        component = item["component"]
        if component not in by_component:
            by_component[component] = []
        by_component[component].append(item["duration_ms"])
    
    # Calculate percentiles
    performance = {}
    for component, latencies in by_component.items():
        sorted_latencies = sorted(latencies)
        count = len(sorted_latencies)
        
        performance[component] = {
            "count": count,
            "avg_ms": round(sum(latencies) / count, 2),
            "min_ms": round(min(latencies), 2),
            "max_ms": round(max(latencies), 2),
            "p50_ms": round(sorted_latencies[int(count * 0.5)], 2),
            "p90_ms": round(sorted_latencies[int(count * 0.9)], 2),
            "p95_ms": round(sorted_latencies[int(count * 0.95)], 2),
            "p99_ms": round(sorted_latencies[int(count * 0.99)], 2) if count > 10 else round(max(latencies), 2)
        }
    
    return {
        "timestamp": datetime.now().isoformat(),
        "performance": performance
    }


@router.get("/errors")
async def get_errors(limit: int = 50):
    """
    Get recent errors
    """
    recent_errors = metrics_store["errors"][-limit:]
    
    # Group by error type
    error_types = {}
    for error in metrics_store["errors"]:
        error_type = error["error_type"]
        if error_type not in error_types:
            error_types[error_type] = 0
        error_types[error_type] += 1
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_errors": len(metrics_store["errors"]),
        "error_types": error_types,
        "recent_errors": recent_errors
    }


@router.get("/cache-stats")
async def get_cache_stats():
    """
    Get cache performance statistics
    """
    total_cache_operations = metrics_store["cache_hits"] + metrics_store["cache_misses"]
    hit_rate = (metrics_store["cache_hits"] / total_cache_operations * 100) if total_cache_operations > 0 else 0
    
    return {
        "timestamp": datetime.now().isoformat(),
        "cache_hits": metrics_store["cache_hits"],
        "cache_misses": metrics_store["cache_misses"],
        "total_operations": total_cache_operations,
        "hit_rate_percent": round(hit_rate, 2)
    }


def calculate_cache_hit_rate():
    """Calculate cache hit rate percentage"""
    total = metrics_store["cache_hits"] + metrics_store["cache_misses"]
    if total == 0:
        return 0
    return round(metrics_store["cache_hits"] / total * 100, 2)


# Middleware to automatically track requests
from fastapi import Request
import time

async def monitoring_middleware(request: Request, call_next):
    """Middleware to track all requests"""
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000
        
        # Record request
        MetricsCollector.record_request(
            endpoint=request.url.path,
            duration_ms=duration_ms,
            status_code=response.status_code
        )
        
        return response
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        # Record error
        MetricsCollector.record_error(
            endpoint=request.url.path,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        
        raise


# Export for use in main.py
__all__ = ["router", "MetricsCollector", "monitoring_middleware"]
