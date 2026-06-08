# agent-capability-registry

Registry of named agent capabilities with enable/disable, tag filtering, prerequisite checking, and JSON-friendly serialization. Pure standard library — **zero runtime dependencies**, fully type-hinted (ships a PEP 561 `py.typed` marker).

When you build an LLM agent you usually have a set of named tools/skills
("web_search", "file_write", "code_execute", ...) that can be turned on or off,
grouped by tags, and may depend on one another. This package gives you a small,
dependency-free object to keep track of them.

## Install

```bash
pip install agent-capability-registry
```

Requires Python 3.9 or newer.

## Usage

```python
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

registry.is_enabled("web_search")   # True
registry.disable("web_search")
registry.enabled_names()            # ["code_execute", "file_write"]

# Check prerequisites
missing = registry.check_prerequisites("code_execute")
# [] — all prerequisites are present and enabled

# Filter by tag
network_caps = registry.filter_by_tag("network")
```

## API

### Registration

```python
cap = registry.register(
    "name",
    "description",
    tags=["tag1", "tag2"],
    enabled=True,
    requires=["other_cap"],
    metadata={"key": "val"},
)
registry.register_or_replace("name", "new description")
```

### Enable / Disable

```python
registry.enable("name")
registry.disable("name")
registry.set_enabled("name", False)
registry.is_enabled("name")    # False for unknown names
```

### Retrieval

```python
registry.get("name")           # Capability, raises KeyError if missing
registry.contains("name")      # bool
registry.names()               # sorted list of all names
registry.enabled_names()       # sorted list of enabled names
registry.disabled_names()      # sorted list of disabled names
registry.all()                 # list[Capability], sorted by name
registry.enabled()             # list of enabled Capability objects
registry.count()               # total registered
registry.enabled_count()       # total enabled
```

### Tag filtering

```python
registry.filter_by_tag("network")          # capabilities with this tag
registry.filter_by_tags(["net", "read"])   # capabilities with ALL tags
registry.all_tags()                        # sorted list of unique tags
```

### Prerequisites

```python
missing = registry.check_prerequisites("code_execute")
# list of prerequisite names that are missing or disabled

ok = registry.prerequisites_satisfied("code_execute")
# True if all prerequisites are registered and enabled
```

### Pythonic access

```python
"web_search" in registry           # bool — same as registry.contains(...)
len(registry)                      # number registered — same as registry.count()
for cap in registry:               # iterate Capability objects, sorted by name
    print(cap.name, cap.enabled)
```

### Serialization

The registry round-trips cleanly through plain JSON-serializable structures,
which makes it easy to persist a set of capabilities to disk or send them over
the wire.

```python
import json

# Capability <-> dict
data = cap.to_dict()
cap = Capability.from_dict(data)        # inverse of to_dict()

# Registry <-> list of dicts
blob = registry.to_list()               # list[dict], sorted by name
json.dump(blob, open("caps.json", "w"))

# Rebuild from saved data
restored = CapabilityRegistry.from_list(json.load(open("caps.json")))

# Merge saved data into an existing registry
registry.load(blob)                     # raises on duplicate names
registry.load(blob, replace=True)       # overwrite existing names instead
```

### Mutation

```python
registry.remove("name")   # raises KeyError if missing
registry.clear()          # remove everything
```

## Capability fields

| Field | Description |
|-------|-------------|
| `name` | Unique identifier (no spaces) |
| `description` | Human-readable description |
| `tags` | String labels for filtering |
| `enabled` | Whether the capability is active |
| `requires` | Names of prerequisite capabilities |
| `metadata` | Arbitrary key/value store |

## Development

The test suite uses only the Python standard library (`unittest`), so no
third-party packages are required to run it:

```bash
python -m unittest discover -s tests
```

Optional linting (install with `pip install -e ".[dev]"`):

```bash
ruff check src tests
```

## License

MIT

