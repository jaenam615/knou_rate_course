"""Rate limiting configuration using slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.constants import RateLimits

limiter = Limiter(key_func=get_remote_address)

RATE_LIMIT_AUTH = RateLimits.AUTH
RATE_LIMIT_WRITE = RateLimits.WRITE
RATE_LIMIT_SEARCH = RateLimits.SEARCH
RATE_LIMIT_DEFAULT = RateLimits.DEFAULT
