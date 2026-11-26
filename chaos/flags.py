"""Fault-flag registry.

Every fault is named FAULT_<AREA>_<NAME>. Flags are read from the environment at
startup and can be overridden at runtime through the /chaos admin endpoint.
The registry is empty on purpose: no faults exist yet.

Descriptions must stay neutral. The registry is readable, so a description
must not reveal the mechanism, or blind game days stop being blind.
"""

from __future__ import annotations

import os
import re
import threading
from dataclasses import dataclass

AREAS = frozenset(
    {
        "INGEST",
        "RETRIEVAL",
        "GATEWAY",
        "AGENT",
        "MCP",
        "GUARD",
        "SERVING",
        "EVAL",
        "OBS",
        "DEPLOY",
    }
)

NAME_RE = re.compile(r"^FAULT_(?P<area>[A-Z]+)_(?P<name>[A-Z0-9]+(?:_[A-Z0-9]+)*)$")
_TRUE = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Fault:
    flag: str
    description: str
    default: str = "0"

    @property
    def area(self) -> str:
        m = NAME_RE.match(self.flag)
        assert m is not None
        return m.group("area")


# Register faults here as labs add them. Empty means no faults exist yet.
REGISTRY: dict[str, Fault] = {}


def validate_name(flag: str) -> None:
    m = NAME_RE.match(flag)
    if m is None:
        raise ValueError(f"{flag!r} does not match FAULT_<AREA>_<NAME>")
    if m.group("area") not in AREAS:
        raise ValueError(f"{flag!r}: unknown area {m.group('area')!r}; allowed: {sorted(AREAS)}")


def register(fault: Fault) -> Fault:
    validate_name(fault.flag)
    if fault.flag in REGISTRY:
        raise ValueError(f"{fault.flag} registered twice")
    REGISTRY[fault.flag] = fault
    return fault


class FlagStore:
    """Env-backed flag values with thread-safe runtime overrides."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._overrides: dict[str, str] = {}

    def value(self, flag: str) -> str:
        if flag not in REGISTRY:
            raise KeyError(f"unregistered fault flag {flag}")
        with self._lock:
            if flag in self._overrides:
                return self._overrides[flag]
        return os.environ.get(flag, REGISTRY[flag].default)

    def is_enabled(self, flag: str) -> bool:
        return self.value(flag).strip().lower() in _TRUE

    def set(self, flag: str, value: str) -> None:
        if flag not in REGISTRY:
            raise KeyError(f"unregistered fault flag {flag}")
        with self._lock:
            self._overrides[flag] = value

    def clear(self) -> None:
        with self._lock:
            self._overrides.clear()

    def snapshot(self) -> dict[str, str]:
        return {flag: self.value(flag) for flag in sorted(REGISTRY)}

    def active(self) -> list[str]:
        return [f for f in sorted(REGISTRY) if self.is_enabled(f)]


STORE = FlagStore()


def is_enabled(flag: str) -> bool:
    return STORE.is_enabled(flag)


def value(flag: str) -> str:
    return STORE.value(flag)
