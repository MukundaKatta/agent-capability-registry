"""Tests for agent_capability_registry."""

from __future__ import annotations

import pytest

from agent_capability_registry import (
    Capability,
    CapabilityRegistry,
    CapabilityRegistryError,
)

# ---------------------------------------------------------------------------
# Capability
# ---------------------------------------------------------------------------


def test_capability_defaults():
    cap = Capability(name="search")
    assert cap.name == "search"
    assert cap.description == ""
    assert cap.tags == []
    assert cap.enabled is True
    assert cap.requires == []
    assert cap.metadata == {}


def test_capability_has_tag_true():
    cap = Capability(name="c", tags=["network", "read"])
    assert cap.has_tag("network") is True


def test_capability_has_tag_false():
    cap = Capability(name="c", tags=["network"])
    assert cap.has_tag("write") is False


def test_capability_has_all_tags_true():
    cap = Capability(name="c", tags=["a", "b", "c"])
    assert cap.has_all_tags(["a", "b"]) is True


def test_capability_has_all_tags_false():
    cap = Capability(name="c", tags=["a", "b"])
    assert cap.has_all_tags(["a", "c"]) is False


def test_capability_has_all_tags_empty():
    cap = Capability(name="c", tags=["a"])
    assert cap.has_all_tags([]) is True


def test_capability_to_dict():
    cap = Capability(
        name="search",
        description="Search the web",
        tags=["network"],
        enabled=True,
        requires=["auth"],
        metadata={"priority": 1},
    )
    d = cap.to_dict()
    assert d["name"] == "search"
    assert d["description"] == "Search the web"
    assert d["tags"] == ["network"]
    assert d["enabled"] is True
    assert d["requires"] == ["auth"]
    assert d["metadata"] == {"priority": 1}


def test_capability_repr_enabled():
    cap = Capability(name="search", tags=["net"])
    r = repr(cap)
    assert "search" in r
    assert "enabled" in r
    assert "net" in r


def test_capability_repr_disabled():
    cap = Capability(name="write", enabled=False)
    r = repr(cap)
    assert "disabled" in r


def test_capability_repr_no_tags():
    cap = Capability(name="x")
    r = repr(cap)
    assert "tags" not in r


# ---------------------------------------------------------------------------
# CapabilityRegistry — registration
# ---------------------------------------------------------------------------


def test_registry_empty():
    reg = CapabilityRegistry()
    assert reg.count() == 0
    assert len(reg) == 0
    assert reg.names() == []
    assert reg.all() == []


def test_registry_register_returns_capability():
    reg = CapabilityRegistry()
    cap = reg.register("search", "Search the web")
    assert isinstance(cap, Capability)
    assert cap.name == "search"
    assert cap.description == "Search the web"


def test_registry_register_with_tags():
    reg = CapabilityRegistry()
    cap = reg.register("search", tags=["network", "read"])
    assert cap.tags == ["network", "read"]


def test_registry_register_with_requires():
    reg = CapabilityRegistry()
    cap = reg.register("code_exec", requires=["file_write"])
    assert cap.requires == ["file_write"]


def test_registry_register_disabled():
    reg = CapabilityRegistry()
    cap = reg.register("search", enabled=False)
    assert cap.enabled is False


def test_registry_register_duplicate_raises():
    reg = CapabilityRegistry()
    reg.register("search")
    with pytest.raises(CapabilityRegistryError):
        reg.register("search")


def test_registry_register_name_with_space_raises():
    reg = CapabilityRegistry()
    with pytest.raises(CapabilityRegistryError):
        reg.register("web search")


def test_registry_register_or_replace():
    reg = CapabilityRegistry()
    reg.register("search", "old")
    cap = reg.register_or_replace("search", "new")
    assert cap.description == "new"
    assert reg.count() == 1


def test_registry_register_or_replace_new():
    reg = CapabilityRegistry()
    cap = reg.register_or_replace("search", "brand new")
    assert cap.name == "search"


# ---------------------------------------------------------------------------
# Enable / Disable
# ---------------------------------------------------------------------------


def test_registry_enable_disable():
    reg = CapabilityRegistry()
    reg.register("search")
    reg.disable("search")
    assert reg.is_enabled("search") is False
    reg.enable("search")
    assert reg.is_enabled("search") is True


def test_registry_enable_missing_raises():
    reg = CapabilityRegistry()
    with pytest.raises(KeyError):
        reg.enable("missing")


def test_registry_disable_missing_raises():
    reg = CapabilityRegistry()
    with pytest.raises(KeyError):
        reg.disable("missing")


def test_registry_set_enabled():
    reg = CapabilityRegistry()
    reg.register("search")
    reg.set_enabled("search", False)
    assert not reg.is_enabled("search")
    reg.set_enabled("search", True)
    assert reg.is_enabled("search")


def test_registry_is_enabled_unknown_returns_false():
    reg = CapabilityRegistry()
    assert reg.is_enabled("ghost") is False


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------


def test_registry_get():
    reg = CapabilityRegistry()
    reg.register("search", "desc")
    cap = reg.get("search")
    assert cap.name == "search"
    assert cap.description == "desc"


def test_registry_get_missing_raises():
    reg = CapabilityRegistry()
    with pytest.raises(KeyError):
        reg.get("missing")


def test_registry_contains_true():
    reg = CapabilityRegistry()
    reg.register("search")
    assert reg.contains("search") is True


def test_registry_contains_false():
    reg = CapabilityRegistry()
    assert reg.contains("search") is False


def test_registry_names_sorted():
    reg = CapabilityRegistry()
    reg.register("zebra")
    reg.register("alpha")
    reg.register("mango")
    assert reg.names() == ["alpha", "mango", "zebra"]


def test_registry_enabled_names():
    reg = CapabilityRegistry()
    reg.register("a")
    reg.register("b", enabled=False)
    reg.register("c")
    assert reg.enabled_names() == ["a", "c"]


def test_registry_disabled_names():
    reg = CapabilityRegistry()
    reg.register("a")
    reg.register("b", enabled=False)
    reg.register("c", enabled=False)
    assert reg.disabled_names() == ["b", "c"]


def test_registry_enabled_list():
    reg = CapabilityRegistry()
    reg.register("a")
    reg.register("b", enabled=False)
    caps = reg.enabled()
    assert len(caps) == 1
    assert caps[0].name == "a"


def test_registry_count():
    reg = CapabilityRegistry()
    reg.register("a")
    reg.register("b")
    assert reg.count() == 2
    assert len(reg) == 2


def test_registry_enabled_count():
    reg = CapabilityRegistry()
    reg.register("a")
    reg.register("b", enabled=False)
    reg.register("c")
    assert reg.enabled_count() == 2


# ---------------------------------------------------------------------------
# Tag filtering
# ---------------------------------------------------------------------------


def test_registry_filter_by_tag():
    reg = CapabilityRegistry()
    reg.register("a", tags=["network"])
    reg.register("b", tags=["network", "read"])
    reg.register("c", tags=["fs"])
    result = reg.filter_by_tag("network")
    names = [c.name for c in result]
    assert "a" in names
    assert "b" in names
    assert "c" not in names


def test_registry_filter_by_tag_includes_disabled():
    reg = CapabilityRegistry()
    reg.register("a", tags=["net"], enabled=False)
    result = reg.filter_by_tag("net")
    assert len(result) == 1


def test_registry_filter_by_tags_all_required():
    reg = CapabilityRegistry()
    reg.register("a", tags=["net", "read"])
    reg.register("b", tags=["net"])
    reg.register("c", tags=["read"])
    result = reg.filter_by_tags(["net", "read"])
    names = [c.name for c in result]
    assert names == ["a"]


def test_registry_all_tags():
    reg = CapabilityRegistry()
    reg.register("a", tags=["net", "read"])
    reg.register("b", tags=["fs", "read"])
    assert reg.all_tags() == ["fs", "net", "read"]


def test_registry_all_tags_empty():
    reg = CapabilityRegistry()
    reg.register("a")
    assert reg.all_tags() == []


# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------


def test_registry_prerequisites_satisfied():
    reg = CapabilityRegistry()
    reg.register("auth")
    reg.register("search", requires=["auth"])
    assert reg.prerequisites_satisfied("search") is True
    assert reg.check_prerequisites("search") == []


def test_registry_prerequisites_missing_cap():
    reg = CapabilityRegistry()
    reg.register("search", requires=["auth"])
    missing = reg.check_prerequisites("search")
    assert "auth" in missing


def test_registry_prerequisites_disabled_cap():
    reg = CapabilityRegistry()
    reg.register("auth", enabled=False)
    reg.register("search", requires=["auth"])
    missing = reg.check_prerequisites("search")
    assert "auth" in missing


def test_registry_prerequisites_multiple_missing():
    reg = CapabilityRegistry()
    reg.register("x", requires=["a", "b", "c"])
    missing = reg.check_prerequisites("x")
    assert sorted(missing) == ["a", "b", "c"]


def test_registry_prerequisites_unknown_capability_raises():
    reg = CapabilityRegistry()
    with pytest.raises(KeyError):
        reg.check_prerequisites("ghost")


def test_registry_prerequisites_no_requires():
    reg = CapabilityRegistry()
    reg.register("standalone")
    assert reg.prerequisites_satisfied("standalone") is True


# ---------------------------------------------------------------------------
# Remove / Clear
# ---------------------------------------------------------------------------


def test_registry_remove():
    reg = CapabilityRegistry()
    reg.register("search")
    reg.remove("search")
    assert not reg.contains("search")
    assert reg.count() == 0


def test_registry_remove_missing_raises():
    reg = CapabilityRegistry()
    with pytest.raises(KeyError):
        reg.remove("ghost")


def test_registry_clear():
    reg = CapabilityRegistry()
    reg.register("a")
    reg.register("b")
    reg.clear()
    assert reg.count() == 0
    assert reg.names() == []


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------


def test_registry_repr():
    reg = CapabilityRegistry()
    reg.register("a")
    reg.register("b", enabled=False)
    r = repr(reg)
    assert "count=2" in r
    assert "enabled=1" in r
