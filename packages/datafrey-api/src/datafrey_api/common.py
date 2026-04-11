from enum import Enum


class Provider(str, Enum):
    snowflake = "snowflake"


class DatabaseStatus(str, Enum):
    loading = "loading"
    connected = "connected"
    disconnected = "disconnected"
    error = "error"
