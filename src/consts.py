from enum import Enum


MAX_PORT: int = 65535


class Protocol(Enum):
    UNKNOWN = "UNKNOWN"
    TCP = "TCP"
    UDP = "UDP"
