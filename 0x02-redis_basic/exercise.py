#!/usr/bin/env python3
""" This module implement a storage Cache class that interfaces with Redis """
import redis
from uuid import uuid4
from typing import Callable, Optional, Any
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """ Decorator function for keeping track of method call count """
    @wraps(method)
    def wrapper(self, *args, **kwds):
        """ Wrapper function to access and modify wrapped function """
        self._redis.incr(method.__qualname__)
        return method(self, *args, **kwds)
    return wrapper


def call_history(method: Callable) -> Callable:
    """ Decorator function for tracking inputs and output histories """
    @wraps(method)
    def wrapper(self, *args, **kwds):
        """ Wrapper function to access and modify wrapped function """
        self._redis.rpush(method.__qualname__ + ":inputs", str(args))
        ret = method(self, *args, **kwds)
        self._redis.rpush(method.__qualname__ + ":outputs", ret)
        return ret
    return wrapper


class Cache:
    """ Cache class implementation """
    def __init__(self):
        """ Creating client instance during initialization """
        self._redis = redis.Redis()
        self._redis.flushdb()

    @count_calls
    @call_history
    def store(self, data: str | bytes | int | float) -> str:
        """ Storage function to Redis server """
        key = str(uuid4())
        if isinstance(data, bytes):
            data = data.decode()
        self._redis.set(key, str(data))
        return key

    @count_calls
    @call_history
    def get(self, key: str, fn: Optional[Callable[[Any],
            Any]] = None) -> str | bytes | int | float:
        """ Retrieval function from Redis server """
        value = self._redis.get(key)
        if fn is None:
            return value
        return fn(value)


def replay(method: Callable) -> None:
    rinst = redis.Redis()
    m_name = method.__qualname__
    count = rinst.get(method.__qualname__).decode("utf-8")
    s = '' if count == 1 else 's'
    print(f"{m_name} was called {count} time{s}:")

    for args, ret in zip(rinst.lrange(m_name + ":inputs", 0, -1),
                         rinst.lrange(m_name + ":outputs", 0, -1)):
        args = args.decode("utf-8")
        ret = ret.decode("utf-8")
        print(f"{m_name}(*{args}) -> {ret}")
