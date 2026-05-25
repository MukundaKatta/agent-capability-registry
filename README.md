# agent-capability-registry

Registry of named agent capabilities with enable/disable, tag filtering, and prerequisite checking. Zero dependencies.

## Install

```bash
pip install agent-capability-registry
```

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

## License

MIT
