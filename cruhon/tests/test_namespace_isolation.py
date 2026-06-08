"""
Test namespace isolation (v0.9a).
Verifies cross-namespace state access is blocked.
"""
import sys
sys.path.insert(0, '..')

from cruhon.core.namespace_runtime import (
    Namespace, reset_registry, get_namespace_registry
)

reset_registry()

print("Testing namespace isolation...")

# Test 1: owning namespace can read its own state
ns_a = Namespace("mod-a")
ns_a.state["secret"] = "abc123"
result = ns_a.access_state("secret", "mod-a")
assert result == "abc123", f"Expected 'abc123', got {result!r}"
print("✓ owner can read own state")

# Test 2: different namespace cannot read state
ns_b = Namespace("mod-b")
ns_b.state["data"] = "sensitive"
try:
    ns_a.access_state("secret", "mod-b")  # mod-b tries to read mod-a's state
    print("✗ should have raised RuntimeError")
    sys.exit(1)
except RuntimeError as e:
    assert "Cross-namespace state access blocked" in str(e)
    print("✓ cross-namespace read blocked")

# Test 3: allowed peer can read state
ns_c = Namespace("mod-c")
ns_c.state["shared"] = "value"
ns_c.allow_peer("mod-a")
result = ns_c.access_state("shared", "mod-a")
assert result == "value"
print("✓ allowed peer can read state")

# Test 4: non-peer still blocked after allow_peer
try:
    ns_c.access_state("shared", "mod-b")  # mod-b not in allowed peers
    print("✗ should have raised RuntimeError")
    sys.exit(1)
except RuntimeError:
    print("✓ non-peer still blocked")

# Test 5: write blocked from other namespace
try:
    ns_a.write_state("secret", "hacked", "mod-b")
    print("✗ should have raised RuntimeError")
    sys.exit(1)
except RuntimeError as e:
    assert "write blocked" in str(e)
    print("✓ cross-namespace write blocked")

# Test 6: write allowed from owning namespace
ns_a.write_state("secret", "new_value", "mod-a")
assert ns_a.state["secret"] == "new_value"
print("✓ owner can write own state")

# Test 7: existing .state dict still works directly (backward compat)
ns_d = Namespace("mod-d")
ns_d.state["key"] = "direct"
assert ns_d.state["key"] == "direct"
print("✓ direct state access backward compatible")

# Test 8: existing tests still pass — run a quick smoke test
print()
print("Running smoke test (existing namespace_runtime tests)...")
from cruhon.core.namespace_runtime import NamespaceRegistry

reg = NamespaceRegistry()
ns_smoke = Namespace("smoke")
ns_smoke.register("greet", lambda args: f"hello {args[0]}")
ns_smoke.init()
assert ns_smoke.call("greet", "world") == "hello world"
print("✓ smoke test passed")

print()
print("All namespace isolation tests passed ✓")
