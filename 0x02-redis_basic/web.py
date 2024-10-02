import requests
import redis
from functools import wraps
from typing import Callable

# Initialize Redis client
r = redis.Redis()


def cache_with_count(method: Callable) -> Callable:
    """Decorator to cache a page and track access count"""
    @wraps(method)
    def wrapper(url: str, *args, **kwargs) -> str:
        """Wrapper function to handle caching and counting"""
        cache_key = f"cached:{url}"
        count_key = f"count:{url}"

        # Check if the content is already in the cache
        cached_content = r.get(cache_key)
        if cached_content:
            # If cached, return the cached content (decoded to string)
            return cached_content.decode("utf-8")

        # If not cached, call the original method (fetch page)
        result = method(url, *args, **kwargs)

        # Cache the result and set expiration time to 10 seconds
        r.setex(cache_key, 10, result)

        # Increment the access count for the URL
        r.incr(count_key)

        return result
    return wrapper


@cache_with_count
def get_page(url: str) -> str:
    """Fetches HTML content from a URL and returns it"""
    response = requests.get(url)
    return response.text
