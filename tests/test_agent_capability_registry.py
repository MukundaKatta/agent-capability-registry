"""Tests for agent_capability_registry.

These use only the Python standard library (``unittest``) so they run with::

    python3 -m unittest discover -s tests

The ``src`` layout is added to ``sys.path`` below so the tests exercise the
real package without requiring an editable install.
"""

from __future__ import annotations

import os
import sys
import unittest

# Make the src-layout package importable without installation.
_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from agent_capability_registry import (  # noqa: E402
    Capability,
    CapabilityRegistry,
    CapabilityRegistryError,
)

# ---------------------------------------------------------------------------
# Capability
# ---------------------------------------------------------------------------


class TestCapability(unittest.TestCase):
    def test_defaults(self):
        cap = Capability(name="search")
        self.assertEqual(cap.name, "search")
        self.assertEqual(cap.description, "")
        self.assertEqual(cap.tags, [])
        self.assertIs(cap.enabled, True)
        self.assertEqual(cap.requires, [])
        self.assertEqual(cap.metadata, {})

    def test_has_tag_true(self):
        cap = Capability(name="c", tags=["network", "read"])
        self.assertIs(cap.has_tag("network"), True)

    def test_has_tag_false(self):
        cap = Capability(name="c", tags=["network"])
        self.assertIs(cap.has_tag("write"), False)

    def test_has_all_tags_true(self):
        cap = Capability(name="c", tags=["a", "b", "c"])
        self.assertIs(cap.has_all_tags(["a", "b"]), True)

    def test_has_all_tags_false(self):
        cap = Capability(name="c", tags=["a", "b"])
        self.assertIs(cap.has_all_tags(["a", "c"]), False)

    def test_has_all_tags_empty(self):
        cap = Capability(name="c", tags=["a"])
        self.assertIs(cap.has_all_tags([]), True)

    def test_to_dict(self):
        cap = Capability(
            name="search",
            description="Search the web",
            tags=["network"],
            enabled=True,
            requires=["auth"],
            metadata={"priority": 1},
        )
        d = cap.to_dict()
        self.assertEqual(d["name"], "search")
        self.assertEqual(d["description"], "Search the web")
        self.assertEqual(d["tags"], ["network"])
        self.assertIs(d["enabled"], True)
        self.assertEqual(d["requires"], ["auth"])
        self.assertEqual(d["metadata"], {"priority": 1})

    def test_to_dict_returns_copies(self):
        # Mutating the returned dict must not affect the capability.
        cap = Capability(name="c", tags=["a"], metadata={"k": "v"})
        d = cap.to_dict()
        d["tags"].append("b")
        d["metadata"]["k"] = "changed"
        self.assertEqual(cap.tags, ["a"])
        self.assertEqual(cap.metadata, {"k": "v"})

    def test_from_dict_full(self):
        data = {
            "name": "search",
            "description": "Search",
            "tags": ["net"],
            "enabled": False,
            "requires": ["auth"],
            "metadata": {"p": 1},
        }
        cap = Capability.from_dict(data)
        self.assertEqual(cap.name, "search")
        self.assertEqual(cap.description, "Search")
        self.assertEqual(cap.tags, ["net"])
        self.assertIs(cap.enabled, False)
        self.assertEqual(cap.requires, ["auth"])
        self.assertEqual(cap.metadata, {"p": 1})

    def test_from_dict_minimal(self):
        cap = Capability.from_dict({"name": "x"})
        self.assertEqual(cap.name, "x")
        self.assertEqual(cap.description, "")
        self.assertEqual(cap.tags, [])
        self.assertIs(cap.enabled, True)

    def test_from_dict_missing_name_raises(self):
        with self.assertRaises(CapabilityRegistryError):
            Capability.from_dict({"description": "no name"})

    def test_from_dict_roundtrip(self):
        cap = Capability(
            name="c",
            description="d",
            tags=["a", "b"],
            enabled=False,
            requires=["r"],
            metadata={"k": "v"},
        )
        self.assertEqual(Capability.from_dict(cap.to_dict()), cap)

    def test_from_dict_does_not_alias_input(self):
        # The capability must not share mutable containers with the input.
        tags = ["a"]
        meta = {"k": "v"}
        cap = Capability.from_dict({"name": "c", "tags": tags, "metadata": meta})
        tags.append("b")
        meta["k"] = "changed"
        self.assertEqual(cap.tags, ["a"])
        self.assertEqual(cap.metadata, {"k": "v"})

    def test_repr_enabled(self):
        cap = Capability(name="search", tags=["net"])
        r = repr(cap)
        self.assertIn("search", r)
        self.assertIn("enabled", r)
        self.assertIn("net", r)

    def test_repr_disabled(self):
        cap = Capability(name="write", enabled=False)
        self.assertIn("disabled", repr(cap))

    def test_repr_no_tags(self):
        cap = Capability(name="x")
        self.assertNotIn("tags", repr(cap))


# ---------------------------------------------------------------------------
# CapabilityRegistry — registration
# ---------------------------------------------------------------------------


class TestRegistration(unittest.TestCase):
    def test_empty(self):
        reg = CapabilityRegistry()
        self.assertEqual(reg.count(), 0)
        self.assertEqual(len(reg), 0)
        self.assertEqual(reg.names(), [])
        self.assertEqual(reg.all(), [])

    def test_register_returns_capability(self):
        reg = CapabilityRegistry()
        cap = reg.register("search", "Search the web")
        self.assertIsInstance(cap, Capability)
        self.assertEqual(cap.name, "search")
        self.assertEqual(cap.description, "Search the web")

    def test_register_with_tags(self):
        reg = CapabilityRegistry()
        cap = reg.register("search", tags=["network", "read"])
        self.assertEqual(cap.tags, ["network", "read"])

    def test_register_with_requires(self):
        reg = CapabilityRegistry()
        cap = reg.register("code_exec", requires=["file_write"])
        self.assertEqual(cap.requires, ["file_write"])

    def test_register_disabled(self):
        reg = CapabilityRegistry()
        cap = reg.register("search", enabled=False)
        self.assertIs(cap.enabled, False)

    def test_register_with_metadata(self):
        reg = CapabilityRegistry()
        cap = reg.register("search", metadata={"priority": 1})
        self.assertEqual(cap.metadata, {"priority": 1})
        self.assertEqual(reg.get("search").metadata, {"priority": 1})

    def test_register_copies_inputs(self):
        # Registry must not alias caller-supplied mutable containers.
        tags = ["a"]
        reg = CapabilityRegistry()
        reg.register("c", tags=tags)
        tags.append("b")
        self.assertEqual(reg.get("c").tags, ["a"])

    def test_register_duplicate_raises(self):
        reg = CapabilityRegistry()
        reg.register("search")
        with self.assertRaises(CapabilityRegistryError):
            reg.register("search")

    def test_register_name_with_space_raises(self):
        reg = CapabilityRegistry()
        with self.assertRaises(CapabilityRegistryError):
            reg.register("web search")

    def test_register_or_replace(self):
        reg = CapabilityRegistry()
        reg.register("search", "old")
        cap = reg.register_or_replace("search", "new")
        self.assertEqual(cap.description, "new")
        self.assertEqual(reg.count(), 1)

    def test_register_or_replace_new(self):
        reg = CapabilityRegistry()
        cap = reg.register_or_replace("search", "brand new")
        self.assertEqual(cap.name, "search")


# ---------------------------------------------------------------------------
# Enable / Disable
# ---------------------------------------------------------------------------


class TestEnableDisable(unittest.TestCase):
    def test_enable_disable(self):
        reg = CapabilityRegistry()
        reg.register("search")
        reg.disable("search")
        self.assertIs(reg.is_enabled("search"), False)
        reg.enable("search")
        self.assertIs(reg.is_enabled("search"), True)

    def test_enable_missing_raises(self):
        reg = CapabilityRegistry()
        with self.assertRaises(KeyError):
            reg.enable("missing")

    def test_disable_missing_raises(self):
        reg = CapabilityRegistry()
        with self.assertRaises(KeyError):
            reg.disable("missing")

    def test_set_enabled(self):
        reg = CapabilityRegistry()
        reg.register("search")
        reg.set_enabled("search", False)
        self.assertFalse(reg.is_enabled("search"))
        reg.set_enabled("search", True)
        self.assertTrue(reg.is_enabled("search"))

    def test_set_enabled_missing_raises(self):
        reg = CapabilityRegistry()
        with self.assertRaises(KeyError):
            reg.set_enabled("missing", True)

    def test_is_enabled_unknown_returns_false(self):
        reg = CapabilityRegistry()
        self.assertIs(reg.is_enabled("ghost"), False)


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------


class TestRetrieval(unittest.TestCase):
    def test_get(self):
        reg = CapabilityRegistry()
        reg.register("search", "desc")
        cap = reg.get("search")
        self.assertEqual(cap.name, "search")
        self.assertEqual(cap.description, "desc")

    def test_get_missing_raises(self):
        reg = CapabilityRegistry()
        with self.assertRaises(KeyError):
            reg.get("missing")

    def test_contains_true(self):
        reg = CapabilityRegistry()
        reg.register("search")
        self.assertIs(reg.contains("search"), True)

    def test_contains_false(self):
        reg = CapabilityRegistry()
        self.assertIs(reg.contains("search"), False)

    def test_dunder_contains(self):
        reg = CapabilityRegistry()
        reg.register("search")
        self.assertIn("search", reg)
        self.assertNotIn("ghost", reg)

    def test_dunder_iter(self):
        reg = CapabilityRegistry()
        reg.register("zebra")
        reg.register("alpha")
        names = [cap.name for cap in reg]
        self.assertEqual(names, ["alpha", "zebra"])

    def test_names_sorted(self):
        reg = CapabilityRegistry()
        reg.register("zebra")
        reg.register("alpha")
        reg.register("mango")
        self.assertEqual(reg.names(), ["alpha", "mango", "zebra"])

    def test_enabled_names(self):
        reg = CapabilityRegistry()
        reg.register("a")
        reg.register("b", enabled=False)
        reg.register("c")
        self.assertEqual(reg.enabled_names(), ["a", "c"])

    def test_disabled_names(self):
        reg = CapabilityRegistry()
        reg.register("a")
        reg.register("b", enabled=False)
        reg.register("c", enabled=False)
        self.assertEqual(reg.disabled_names(), ["b", "c"])

    def test_enabled_list(self):
        reg = CapabilityRegistry()
        reg.register("a")
        reg.register("b", enabled=False)
        caps = reg.enabled()
        self.assertEqual(len(caps), 1)
        self.assertEqual(caps[0].name, "a")

    def test_count(self):
        reg = CapabilityRegistry()
        reg.register("a")
        reg.register("b")
        self.assertEqual(reg.count(), 2)
        self.assertEqual(len(reg), 2)

    def test_enabled_count(self):
        reg = CapabilityRegistry()
        reg.register("a")
        reg.register("b", enabled=False)
        reg.register("c")
        self.assertEqual(reg.enabled_count(), 2)


# ---------------------------------------------------------------------------
# Tag filtering
# ---------------------------------------------------------------------------


class TestTagFiltering(unittest.TestCase):
    def test_filter_by_tag(self):
        reg = CapabilityRegistry()
        reg.register("a", tags=["network"])
        reg.register("b", tags=["network", "read"])
        reg.register("c", tags=["fs"])
        names = [c.name for c in reg.filter_by_tag("network")]
        self.assertIn("a", names)
        self.assertIn("b", names)
        self.assertNotIn("c", names)

    def test_filter_by_tag_includes_disabled(self):
        reg = CapabilityRegistry()
        reg.register("a", tags=["net"], enabled=False)
        self.assertEqual(len(reg.filter_by_tag("net")), 1)

    def test_filter_by_tags_all_required(self):
        reg = CapabilityRegistry()
        reg.register("a", tags=["net", "read"])
        reg.register("b", tags=["net"])
        reg.register("c", tags=["read"])
        names = [c.name for c in reg.filter_by_tags(["net", "read"])]
        self.assertEqual(names, ["a"])

    def test_all_tags(self):
        reg = CapabilityRegistry()
        reg.register("a", tags=["net", "read"])
        reg.register("b", tags=["fs", "read"])
        self.assertEqual(reg.all_tags(), ["fs", "net", "read"])

    def test_all_tags_empty(self):
        reg = CapabilityRegistry()
        reg.register("a")
        self.assertEqual(reg.all_tags(), [])


# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------


class TestPrerequisites(unittest.TestCase):
    def test_satisfied(self):
        reg = CapabilityRegistry()
        reg.register("auth")
        reg.register("search", requires=["auth"])
        self.assertIs(reg.prerequisites_satisfied("search"), True)
        self.assertEqual(reg.check_prerequisites("search"), [])

    def test_missing_cap(self):
        reg = CapabilityRegistry()
        reg.register("search", requires=["auth"])
        self.assertIn("auth", reg.check_prerequisites("search"))

    def test_disabled_cap(self):
        reg = CapabilityRegistry()
        reg.register("auth", enabled=False)
        reg.register("search", requires=["auth"])
        self.assertIn("auth", reg.check_prerequisites("search"))

    def test_multiple_missing(self):
        reg = CapabilityRegistry()
        reg.register("x", requires=["a", "b", "c"])
        self.assertEqual(sorted(reg.check_prerequisites("x")), ["a", "b", "c"])

    def test_unknown_capability_raises(self):
        reg = CapabilityRegistry()
        with self.assertRaises(KeyError):
            reg.check_prerequisites("ghost")

    def test_no_requires(self):
        reg = CapabilityRegistry()
        reg.register("standalone")
        self.assertIs(reg.prerequisites_satisfied("standalone"), True)


# ---------------------------------------------------------------------------
# Remove / Clear
# ---------------------------------------------------------------------------


class TestRemoveClear(unittest.TestCase):
    def test_remove(self):
        reg = CapabilityRegistry()
        reg.register("search")
        reg.remove("search")
        self.assertFalse(reg.contains("search"))
        self.assertEqual(reg.count(), 0)

    def test_remove_missing_raises(self):
        reg = CapabilityRegistry()
        with self.assertRaises(KeyError):
            reg.remove("ghost")

    def test_clear(self):
        reg = CapabilityRegistry()
        reg.register("a")
        reg.register("b")
        reg.clear()
        self.assertEqual(reg.count(), 0)
        self.assertEqual(reg.names(), [])


# ---------------------------------------------------------------------------
# Serialisation (to_list / load / from_list)
# ---------------------------------------------------------------------------


class TestSerialisation(unittest.TestCase):
    def _populate(self) -> CapabilityRegistry:
        reg = CapabilityRegistry()
        reg.register("file_write", "Write files", tags=["fs", "write"])
        reg.register(
            "code_exec",
            "Run code",
            tags=["compute"],
            enabled=False,
            requires=["file_write"],
            metadata={"sandbox": True},
        )
        return reg

    def test_to_list_sorted_by_name(self):
        reg = self._populate()
        names = [d["name"] for d in reg.to_list()]
        self.assertEqual(names, ["code_exec", "file_write"])

    def test_to_list_is_json_serialisable(self):
        import json

        reg = self._populate()
        # Should not raise.
        text = json.dumps(reg.to_list())
        self.assertIn("file_write", text)

    def test_from_list_roundtrip(self):
        reg = self._populate()
        rebuilt = CapabilityRegistry.from_list(reg.to_list())
        self.assertEqual(rebuilt.to_list(), reg.to_list())
        self.assertIs(rebuilt.is_enabled("file_write"), True)
        self.assertIs(rebuilt.is_enabled("code_exec"), False)
        self.assertEqual(rebuilt.get("code_exec").requires, ["file_write"])
        self.assertEqual(rebuilt.get("code_exec").metadata, {"sandbox": True})

    def test_load_into_existing(self):
        reg = CapabilityRegistry()
        reg.register("existing")
        reg.load([{"name": "loaded", "tags": ["t"]}])
        self.assertEqual(reg.names(), ["existing", "loaded"])
        self.assertEqual(reg.get("loaded").tags, ["t"])

    def test_load_duplicate_without_replace_raises(self):
        reg = CapabilityRegistry()
        reg.register("dup", "original")
        with self.assertRaises(CapabilityRegistryError):
            reg.load([{"name": "dup", "description": "new"}])

    def test_load_duplicate_with_replace(self):
        reg = CapabilityRegistry()
        reg.register("dup", "original")
        reg.load([{"name": "dup", "description": "new"}], replace=True)
        self.assertEqual(reg.get("dup").description, "new")
        self.assertEqual(reg.count(), 1)

    def test_load_missing_name_raises(self):
        reg = CapabilityRegistry()
        with self.assertRaises(CapabilityRegistryError):
            reg.load([{"description": "no name"}])

    def test_load_name_with_space_raises(self):
        reg = CapabilityRegistry()
        with self.assertRaises(CapabilityRegistryError):
            reg.load([{"name": "bad name"}])

    def test_from_list_empty(self):
        reg = CapabilityRegistry.from_list([])
        self.assertEqual(reg.count(), 0)


# ---------------------------------------------------------------------------
# Repr
# ---------------------------------------------------------------------------


class TestRepr(unittest.TestCase):
    def test_registry_repr(self):
        reg = CapabilityRegistry()
        reg.register("a")
        reg.register("b", enabled=False)
        r = repr(reg)
        self.assertIn("count=2", r)
        self.assertIn("enabled=1", r)


if __name__ == "__main__":
    unittest.main()
