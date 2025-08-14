import os
from typing import Iterable

from prometheus_client.core import CounterMetricFamily, HistogramMetricFamily
from prometheus_client.registry import Collector

from app.core.redis_client import get_redis

# Keys used by the worker
_METRICS = {
    "tagging_tasks_total": {
        "success": "metrics:tasks_total:success",
        "failure": "metrics:tasks_total:failure",
        "timeout": "metrics:tasks_total:timeout"
    },
    "tagging_cache_hits_total": {
        "hit": "metrics:cache_hits_total"
    }
}

_HIST_PREFIX = "metrics:task_duration_ms"
_HIST_BUCKETS_MS = [50, 100, 250, 500, 1000, 2000, 5000] # +Inf implicit

def _queue_len(redis, name: str) -> int:
    """
    Return the length of the Celery Redis queue.
    """
    try_keys = [name, f"queue:{name}"]
    for key in try_keys:
        try:
            num = redis.llen(key)
            if num is not None and num >= 0:
                return int(num)
        except Exception:
            pass
    return 0

class RedisCeleryCollector(Collector):
    def collect(self) -> Iterable[CounterMetricFamily]:
        redis = get_redis()
        
        # Tasks counter with status label
        counter = CounterMetricFamily(
            "tagging_tasks_total",
            "Total Celery tagging tasks by final status",
            labels=["status"]
        )
        for label, key in _METRICS["tagging_tasks_total"].items():
            try:
                val = int(redis.get(key) or 0)
            except Exception:
                val = 0
            counter.add_metric([label], val)
        yield counter
        
        # Cache hits (no labels)
        cache_hits = CounterMetricFamily(
            "tagging_cache_hits_total",
            "Total cache hits in tagging worker",
            labels=[]
        )
        try:
            val = int(redis.get(_METRICS["tagging_cache_hits_total"]["hit"]) or 0)
        except Exception:
            val = 0
        cache_hits.add_metric([], val)
        yield cache_hits
        
        # Queue length gauge
        queue_name = os.getenv("CELERY_TAGGING_QUEUE", "tagging")
        queue_len = _queue_len(redis, queue_name)
        gauge = CounterMetricFamily(
            "tagging_queue_length",
            f"Current backlog (LLEN) of Celery queue '{queue_name}'",
            labels=[]
        )
        gauge.add_metric([], queue_len)
        yield gauge
        
        # Task duration histogram
        buckets = []
        for bucket in _HIST_BUCKETS_MS:
            try:
                val = int(redis.get(f"{_HIST_PREFIX}:bucket:le_{bucket}") or 0)
            except Exception:
                val = 0
            buckets.append((float(bucket) / 1000.0, val))
        
        try:
            inf_val = int(redis.get(f"{_HIST_PREFIX}:bucket:le_inf") or 0)
        except Exception:
            inf_val = 0
        buckets.append((float("inf"), inf_val))
        
        try:
            hist_sum = float(redis.get(f"{_HIST_PREFIX}:sum") or 0.0)
            hist_count = int(redis.get(f"{_HIST_PREFIX}:count") or 0)
        except Exception:
            hist_sum, hist_count = 0.0, 0
        
        histogram = HistogramMetricFamily(
            "tagging_task_duration_seconds",
            "Distribution of tagging Celery task durations (seconds)",
            labels=[]
        )
        histogram.add_sample("tagging_task_duration_seconds_sum", labels=[], value=hist_sum)
        histogram.add_sample("tagging_task_duration_seconds_count", labels=[], value=hist_count)
        
        for le, count in buckets:
            histogram.add_sample(
                "tagging_task_duration_seconds_bucket",
                labels={"le": str(le)},
                value=count
            )
        yield histogram
