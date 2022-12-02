from typing import Optional, Any


class BaseCommand:
    """Base class for socket-message commands"""

    name: str = ...
    """A unique command name used to identify it"""

    data_length: int = ...
    """Length of command data in bytes"""

    def __call__(self, session_data: Any) -> Optional['BaseCommand']:
        return None

    def __bytes__(self) -> bytes:
        try:
            return self.to_bytes()
        except NotImplementedError:
            return NotImplemented

    @classmethod
    def from_bytes(cls, data_bytes: bytes) -> 'BaseCommand':
        """Constructs command from its data bytes"""
        raise NotImplementedError

    def to_bytes(self) -> bytes:
        """Converts command's data to bytes"""
        raise NotImplementedError
