import math
from typing import Protocol

from .basecommand import BaseCommand
from .boolcommand import BoolCommand

__all__ = ['IsPrimeCommand']


class IsPrimeSessionData(Protocol):
    numbers_cnt: int
    primes_cnt: int
    min_value: int
    max_value: int


class IsPrimeCommand(BaseCommand):
    """isprime(n) command"""

    MAX_ALLOWED = 2 ** 31 - 1
    MIN_ALLOWED = - 2 ** 31

    name = "isprime"
    data_length = 4  # one 32-bit integer

    def __init__(self, n: int) -> None:
        if not self.MIN_ALLOWED <= n <= self.MAX_ALLOWED:
            raise OverflowError
        self.n = n

    def __call__(self, session_data: IsPrimeSessionData) -> BoolCommand:
        session_data.numbers_cnt += 1
        session_data.max_value = max(self.n, session_data.max_value)
        session_data.min_value = min(self.n, session_data.min_value)

        is_prime = self._is_prime(self.n)
        if is_prime:
            session_data.primes_cnt += 1

        return BoolCommand(is_prime)

    def __str__(self):
        return f'isprime({self.n})'

    def __repr__(self):
        return f'{self.__class__.name}(n={self.n})'

    @classmethod
    def from_bytes(cls, data_bytes: bytes) -> 'BaseCommand':
        n = int.from_bytes(data_bytes, byteorder='little', signed=True)
        return cls(n)

    def to_bytes(self) -> bytes:
        return self.n.to_bytes(self.data_length, "little", signed=True)

    @staticmethod
    def _is_prime(n: int) -> bool:
        if n < 2:
            return False
        sqrt_n = int(math.sqrt(n))
        for d in range(2, sqrt_n + 1):
            if n % d == 0:
                return False
        return True
