"""Broker Dramatiq (Redis). Un solo import configura actor global + resultados.

Redis via env: REDIS_URL (colas, DB 0) — en compose es redis://redis:6379/0,
en local cae a redis://127.0.0.1:6379/0. Resultados en la misma instancia,
DB 1 (o REDIS_RESULTS_URL si se define explicito).
"""
import logging
import os
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend

log = logging.getLogger("sismos.middleware")

REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")

def _results_url(base: str) -> str:
    head, _, tail = base.rpartition("/")
    return f"{head}/1" if tail.isdigit() else base

RESULTS_URL = os.environ.get("REDIS_RESULTS_URL", _results_url(REDIS_URL))

class SpyMiddleware(dramatiq.Middleware):
    def before_nack(self, broker, message):
        log.warning("NACK %s actor=%s", message.message_id, message.actor_name)

    def after_nack(self, broker, message):
        log.warning("NACKED %s", message.message_id)

broker = RedisBroker(url=REDIS_URL)
broker.add_middleware(SpyMiddleware())
broker.add_middleware(Results(backend=RedisBackend(url=RESULTS_URL)))
dramatiq.set_broker(broker)
