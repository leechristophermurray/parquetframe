#!/usr/bin/env python3
"""
Test script to verify Phase 1 deprecation warnings work correctly.

This script tests:
1. Phase 2 imports work without warnings
2. Phase 1 imports raise DeprecationWarning
"""

import sys
import warnings

print("=" * 80)
print("Testing Phase 2 and Phase 1 API deprecation warnings")
print("=" * 80)

# Test 1: Phase 2 imports should NOT raise warnings
print("\n[Test 1] Phase 2 imports (should work without warnings)...")
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")

    if len(w) == 0:
        print("✓ Phase 2 imports work without warnings")
    else:
        print(f"✗ FAILED: Phase 2 imports raised {len(w)} warning(s)")
        for warning in w:
            print(f"  - {warning.category.__name__}: {warning.message}")
        sys.exit(1)

# Test 2: Phase 1 imports should raise DeprecationWarning
print("\n[Test 2] Phase 1 imports (should raise DeprecationWarning)...")
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")

    if len(w) >= 1:
        found_deprecation = any(
            issubclass(warning.category, DeprecationWarning) for warning in w
        )
        if found_deprecation:
            has_deprecated_msg = any(
                "deprecated" in str(warning.message).lower() for warning in w
            )
            if has_deprecated_msg:
                print("✓ Phase 1 imports raise DeprecationWarning with correct message")
            else:
                print("✗ FAILED: DeprecationWarning doesn't contain 'deprecated'")
                sys.exit(1)
        else:
            print(
                f"✗ FAILED: Expected DeprecationWarning, got: {[w.category.__name__ for w in w]}"
            )
            sys.exit(1)
    else:
        print("✗ FAILED: Phase 1 imports did not raise any warning")
        sys.exit(1)

# Test 3: FORMAT_HANDLERS should also be deprecated
print("\n[Test 3] Phase 1 FORMAT_HANDLERS (should raise DeprecationWarning)...")
with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")

    if len(w) >= 1 and any(
        issubclass(warning.category, DeprecationWarning) for warning in w
    ):
        print("✓ FORMAT_HANDLERS raises DeprecationWarning")
    else:
        print("✗ FAILED: FORMAT_HANDLERS did not raise DeprecationWarning")
        sys.exit(1)

# Test 4: Invalid imports should raise AttributeError
print("\n[Test 4] Invalid imports (should raise AttributeError)...")
try:
    from parquetframe.core import NonExistentClass  # noqa: F401

    print("✗ FAILED: Invalid import did not raise AttributeError")
    sys.exit(1)
except AttributeError as e:
    if "has no attribute" in str(e):
        print("✓ Invalid imports raise AttributeError with correct message")
    else:
        print(f"✗ FAILED: AttributeError has wrong message: {e}")
        sys.exit(1)

print("\n" + "=" * 80)
print("All deprecation tests passed!")
print("=" * 80)
