"""Registry of named agent capabilities."""

from __future__ import annotations

from .core import Capability, CapabilityRegistry, CapabilityRegistryError

__all__ = [
    "Capability",
    "CapabilityRegistry",
    "CapabilityRegistryError",
]
