"""Registry of named agent capabilities with enable/disable, tags, and prerequisites.

Example::

    from agent_capability_registry import CapabilityRegistry

    registry = CapabilityRegistry()

    registry.register("web_search", "Search the web", tags=["network", "read"])
    registry.register("file_write", "Write files to disk", tags=["fs", "write"])
    registry.register(
        "code_execute",
        "Run code in a sandbox",
        tags=["compute"],
        requires=["file_write"],
    )

    registry.is_enabled("web_search")           # True
    registry.disable("web_search")
    registry.enabled_names()                    # ["code_execute", "file_write"]

    missing = registry.check_prerequisites("code_execute")
    # [] — all prerequisites are present and enabled

    network_caps = registry.filter_by_tag("network")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class CapabilityRegistryError(Exception):
    """Raised for invalid operations on the registry."""


@dataclass
class Capability:
    """A named agent capability.

    Attributes:
        name:        Unique identifier (no spaces).
        description: Human-readable description.
        tags:        Optional list of string labels.
        enabled:     Whether the capability is currently active.
        requires:    Names of capabilities this one depends on.
        metadata:    Arbitrary key/value store.
    """

    name: str
    description: str = ""
    tags: list[str] = field(default_factory=list)
    enabled: bool = True
    requires: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def has_tag(self, tag: str) -> bool:
        """``True`` if *tag* is in this capability's tags."""
        return tag in self.tags

    def has_all_tags(self, tags: list[str]) -> bool:
        """``True`` if all *tags* are present."""
        return all(t in self.tags for t in tags)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {
            "name": self.name,
            "description": self.description,
            "tags": list(self.tags),
            "enabled": self.enabled,
            "requires": list(self.requires),
            "metadata": dict(self.metadata),
        }

    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        tag_str = f", tags={self.tags}" if self.tags else ""
        return f"Capability({self.name!r}, {status}{tag_str})"


class CapabilityRegistry:
    """Register, query, and manage agent capabilities.

    Example::

        registry = CapabilityRegistry()
        registry.register("search", "Web search", tags=["network"])
        registry.register("write", "File writer", tags=["fs"])
        registry.disable("search")
        registry.enabled_names()   # ["write"]
        registry.all_tags()        # ["fs", "network"]
    """

    def __init__(self) -> None:
        self._caps: dict[str, Capability] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        description: str = "",
        *,
        tags: list[str] | None = None,
        enabled: bool = True,
        requires: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Capability:
        """Register a new capability.

        Args:
            name:        Unique name (no spaces).
            description: Human-readable description.
            tags:        Optional string labels.
            enabled:     Whether the capability starts enabled.
            requires:    Names of prerequisite capabilities.
            metadata:    Arbitrary key/value metadata.

        Returns:
            The new :class:`Capability`.

        Raises:
            CapabilityRegistryError: If *name* contains spaces or is already
                registered.
        """
        if " " in name:
            raise CapabilityRegistryError(
                f"Capability name must not contain spaces: {name!r}"
            )
        if name in self._caps:
            raise CapabilityRegistryError(f"Capability already registered: {name!r}")
        cap = Capability(
            name=name,
            description=description,
            tags=list(tags) if tags else [],
            enabled=enabled,
            requires=list(requires) if requires else [],
            metadata=dict(metadata) if metadata else {},
        )
        self._caps[name] = cap
        return cap

    def register_or_replace(
        self,
        name: str,
        description: str = "",
        *,
        tags: list[str] | None = None,
        enabled: bool = True,
        requires: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Capability:
        """Register a capability, replacing any existing one with the same name."""
        if name in self._caps:
            del self._caps[name]
        return self.register(
            name,
            description,
            tags=tags,
            enabled=enabled,
            requires=requires,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Enable / Disable
    # ------------------------------------------------------------------

    def enable(self, name: str) -> None:
        """Enable a capability by name.

        Raises:
            KeyError: If the capability does not exist.
        """
        self._get_or_raise(name).enabled = True

    def disable(self, name: str) -> None:
        """Disable a capability by name.

        Raises:
            KeyError: If the capability does not exist.
        """
        self._get_or_raise(name).enabled = False

    def set_enabled(self, name: str, value: bool) -> None:
        """Set the enabled state of a capability."""
        self._get_or_raise(name).enabled = value

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get(self, name: str) -> Capability:
        """Return the capability with *name*.

        Raises:
            KeyError: If the capability does not exist.
        """
        return self._get_or_raise(name)

    def contains(self, name: str) -> bool:
        """``True`` if a capability with *name* exists."""
        return name in self._caps

    def is_enabled(self, name: str) -> bool:
        """``True`` if the capability exists *and* is enabled.

        Returns ``False`` for unknown names rather than raising.
        """
        cap = self._caps.get(name)
        return cap is not None and cap.enabled

    def names(self) -> list[str]:
        """Sorted list of all capability names."""
        return sorted(self._caps)

    def enabled_names(self) -> list[str]:
        """Sorted list of names for enabled capabilities."""
        return sorted(n for n, c in self._caps.items() if c.enabled)

    def disabled_names(self) -> list[str]:
        """Sorted list of names for disabled capabilities."""
        return sorted(n for n, c in self._caps.items() if not c.enabled)

    def all(self) -> list[Capability]:
        """All capabilities sorted by name."""
        return [self._caps[n] for n in sorted(self._caps)]

    def enabled(self) -> list[Capability]:
        """All enabled capabilities sorted by name."""
        return [c for c in self.all() if c.enabled]

    def count(self) -> int:
        """Total number of registered capabilities."""
        return len(self._caps)

    def enabled_count(self) -> int:
        """Number of enabled capabilities."""
        return sum(1 for c in self._caps.values() if c.enabled)

    # ------------------------------------------------------------------
    # Tag filtering
    # ------------------------------------------------------------------

    def filter_by_tag(self, tag: str) -> list[Capability]:
        """All capabilities (enabled or not) that have *tag*."""
        return [c for c in self.all() if c.has_tag(tag)]

    def filter_by_tags(self, tags: list[str]) -> list[Capability]:
        """All capabilities that have ALL of *tags*."""
        return [c for c in self.all() if c.has_all_tags(tags)]

    def all_tags(self) -> list[str]:
        """Sorted list of all unique tags across all capabilities."""
        tags: set[str] = set()
        for c in self._caps.values():
            tags.update(c.tags)
        return sorted(tags)

    # ------------------------------------------------------------------
    # Prerequisites
    # ------------------------------------------------------------------

    def check_prerequisites(self, name: str) -> list[str]:
        """Return names of prerequisites that are missing or disabled.

        A prerequisite is considered satisfied when it is registered *and*
        enabled.

        Args:
            name: Capability to check.

        Returns:
            List of unsatisfied prerequisite names (empty → all satisfied).

        Raises:
            KeyError: If *name* is not registered.
        """
        cap = self._get_or_raise(name)
        missing: list[str] = []
        for req in cap.requires:
            if not self.is_enabled(req):
                missing.append(req)
        return missing

    def prerequisites_satisfied(self, name: str) -> bool:
        """``True`` if all prerequisites of *name* are enabled."""
        return len(self.check_prerequisites(name)) == 0

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def remove(self, name: str) -> None:
        """Remove a capability by name.

        Raises:
            KeyError: If the capability does not exist.
        """
        self._get_or_raise(name)
        del self._caps[name]

    def clear(self) -> None:
        """Remove all capabilities."""
        self._caps.clear()

    # ------------------------------------------------------------------
    # Dunder
    # ------------------------------------------------------------------

    def __len__(self) -> int:
        return len(self._caps)

    def __repr__(self) -> str:
        return (
            f"CapabilityRegistry(count={self.count()}, enabled={self.enabled_count()})"
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_or_raise(self, name: str) -> Capability:
        cap = self._caps.get(name)
        if cap is None:
            raise KeyError(f"No capability registered: {name!r}")
        return cap
