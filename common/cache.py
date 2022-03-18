"""
基于内存缓存
"""
import time


class Value:
    def __init__(self, value, put_time, expired):
        """
        缓存值对象

        :param value: 具体的值
        :param put_time: 放入缓存的时间
        :param expired: 缓存失效时间
        """
        self.value = value
        self.put_time = put_time
        self.expired = expired

    def __str__(self):
        return f"${self.value} + '--' + ${self.put_time} + '--' + ${self.expired}"


class MemoryCache:

    def __init__(self):
        self.__cache = {}

    def set_value(self, k, v, expired):
        """
        将值放入缓存中

        :param k: 缓存的 key
        :param v: 缓存值
        :param expired: 缓存失效时间，单位秒(s)
        """
        # 获取当前时间戳 10 位 秒级
        current_timestamp = int(time.time())
        self.__cache[k] = Value(v, current_timestamp, expired)

    def check_key(self, k):
        """
        检查缓存是否可用

        :param k: 缓存 key
        :return: True or False
        """
        current_timestamp = int(time.time())
        value = self.__cache.get(k, None)
        # 考虑k不存在的情况
        if value is None:
            return False
        differ = current_timestamp - value.put_time
        if differ > value.expired:
            # 证明缓存失效了，删除键值对
            del self.__cache[k]
            return False
        return True

    def get_value(self, k):
        if self.check_key(k):
            return self.__cache[k].value
        return None


memory_cache = MemoryCache()
