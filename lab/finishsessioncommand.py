from typing import Protocol

from lab.basecommand import BaseCommand

__all__ = ['FinishSessionCommand']

from lab.statscommand import StatsCommand


class IsPrimeSessionData(Protocol):
    session_running: bool

    numbers_cnt: int
    primes_cnt: int
    min_value: int
    max_value: int


class FinishSessionCommand(BaseCommand):
    """finishsession()"""

    name = 'finishsession'
    data_length = 0

    def __call__(self, session_data: IsPrimeSessionData) -> StatsCommand:
        session_data.session_running = False
        return StatsCommand(
            numbers_cnt=session_data.numbers_cnt,
            primes_cnt=session_data.primes_cnt,
            min_value=session_data.min_value,
            max_value=session_data.max_value
        )

    def __str__(self):
        return self.name + '()'

    def __repr__(self):
        return self.__class__.name + '()'

    @classmethod
    def from_bytes(cls, data_bytes: bytes) -> 'BaseCommand':
        return cls()

    def to_bytes(self) -> bytes:
        return bytes()

