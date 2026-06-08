"""Test namespace_runtime.py directly."""
import sys
sys.path.insert(0, '..')
from cruhon.core.namespace_runtime import (
    Namespace, NamespaceRegistry, reset_registry, get_namespace_registry
)

reset_registry()

# Test 1: basic register + call
ns = Namespace("test")
ns.register("greet", lambda args: f"Hello {args[0]}")
ns.init()
result = ns.call("greet", "World")
assert result == "Hello World", f"Expected 'Hello World', got {result!r}"
print("✓ basic call")

# Test 2: init hook
fired = []
ns2 = Namespace("test2")
ns2.hook("init", lambda n: fired.append("init"))
ns2.init()
assert "init" in fired
print("✓ init hook")

# Test 3: state
ns3 = Namespace("test3")
ns3.state["token"] = "abc123"
assert ns3.state["token"] == "abc123"
print("✓ state")

# Test 4: registry
reg = get_namespace_registry()
reg.register("myns", ns)
assert reg["myns"] is ns
print("✓ registry lookup")

# Test 5: missing method raises RuntimeError
try:
    ns.call("nonexistent")
    print("✗ should have raised")
except RuntimeError as e:
    assert "nonexistent" in str(e)
    print("✓ missing method error")

print("\nAll namespace_runtime tests passed")
