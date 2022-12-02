import struct

from lab.basecommand import BaseCommand


class StatsCommand(BaseCommand):
    """stats(numbers_cnt, primes_cnt, min_value, max_value)"""

    name = 'stats'
    data_length = 4 * 4  # 4 32-bit integers

    def __init__(self, numbers_cnt: int, primes_cnt: int, min_value: int, max_value: int) -> None:
        self.max_value = max_value
        self.min_value = min_value
        self.primes_cnt = primes_cnt
        self.numbers_cnt = numbers_cnt

    def __str__(self):
        return self.name + f'({self.numbers_cnt}, {self.primes_cnt}, {self.min_value}, {self.max_value})'

    def __repr__(self):
        return self.__class__.__name__ + f'(numbers_cnt={self.numbers_cnt}, primes_cnt={self.primes_cnt}, ' \
                                         f'min_value={self.min_value}, max_value={self.max_value})'

    @classmethod
    def from_bytes(cls, data_bytes: bytes) -> 'BaseCommand':
        args = struct.unpack('<iiii', data_bytes)
        return cls(*args)

    def to_bytes(self) -> bytes:
        return struct.pack('<iiii', self.numbers_cnt, self.primes_cnt, self.min_value, self.max_value)
