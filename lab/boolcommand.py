from .basecommand import BaseCommand


class BoolCommand(BaseCommand):
    """`bool` command

     Supports to arguments:
     - `bool(1)` that means True
     - `bool(0)` that means False
     """

    name = 'bool'
    data_length = 1

    def __init__(self, value: bool) -> None:
        self.value = value

    def __str__(self):
        return f'bool({int(self.value)})'

    def __repr__(self):
        return f'{self.__class__.name}(value={self.value})'

    @classmethod
    def from_bytes(cls, data_bytes: bytes) -> 'BaseCommand':
        value = int.from_bytes(data_bytes, byteorder="little")
        if value not in [0, 1]:
            raise ValueError('Value should be 0 or 1')
        return cls(bool(value))

    def to_bytes(self) -> bytes:
        return self.value.to_bytes(self.data_length, 'little')
