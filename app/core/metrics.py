import os

from typing import Iterable
from prometheus_client.core import CounterMetricFamily
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
