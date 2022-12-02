from typing import Optional

from .basecommand import BaseCommand


class WhoCommand(BaseCommand):
    """who(author) or who("")

    If author is not given who(AUTHOR) returned."""

    name = 'who'
    data_length = 128

    def __init__(self, author: Optional[str] = None):
        self.author = author

    def __call__(self, session_data):
        if not self.author:
            return WhoCommand(session_data.author)

    def __str__(self):
        if self.author:
            return f'{self.name}("{self.author}")'
        return self.name + '()'

    def __repr__(self):
        return self.__class__.__name__ + f'(author={self.author!r})'

    @classmethod
    def from_bytes(cls, data_bytes: bytes) -> 'BaseCommand':
        author = data_bytes.strip(b'\0').decode() or None
        return cls(author)

    def to_bytes(self) -> bytes:
        if not self.author:
            return b'\0' * self.data_length
        author = self.author.encode(errors='skip').ljust(self.data_length, b'\0')
        if len(author) > self.data_length:
            raise ValueError(f"'{author}' is too long")
        return author
