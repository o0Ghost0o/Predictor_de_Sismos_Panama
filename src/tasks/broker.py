"""Broker Dramatiq (Redis local). Un solo import configura actor global + resultados."""
import logging
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.results import Results
from dramatiq.results.backends import RedisBackend

log = logging.getLogger("sismos.middleware")

class SpyMiddleware(dramatiq.Middleware):
    def before_nack(self, broker, message):
        log.warning("NACK %s actor=%s", message.message_id, message.actor_name)

    def after_nack(self, broker, message):
        log.warning("NACKED %s", message.message_id)

broker = RedisBroker(url="redis://127.0.0.1:6379/0")
broker.add_middleware(SpyMiddleware())
broker.add_middleware(Results(backend=RedisBackend(url="redis://127.0.0.1:6379/1")))
dramatiq.set_broker(broker)
