#!/usr/bin/env python3
"""
Test script to verify Phase 1 deprecation warnings work correctly.

This script tests:
1. Phase 2 imports work without warnings
2. Phase 1 imports raise DeprecationWarning
"""

import subprocess
import sys

print("=" * 80)
print("Testing Phase 2 and Phase 1 API deprecation warnings")
print("=" * 80)

# Test 1: Phase 2 imports should NOT raise warnings
print("\n[Test 1] Phase 2 imports (should work without warnings)...")
result = subprocess.run(
    [
        sys.executable,
        "-W",
        "all",
        "-c",
        "from parquetframe.core import DataFrameProxy, read, read_parquet",
    ],
    capture_output=True,
    text=True,
)

if "DeprecationWarning" in result.stderr or "deprecated" in result.stderr.lower():
    print("✗ FAILED: Phase 2 imports raised deprecation warnings")
    print("Warnings:")
    print(result.stderr)
    sys.exit(1)
else:
    print("✓ Phase 2 imports work without warnings")
# Test 2: Phase 1 imports should raise DeprecationWarning
print("\n[Test 2] Phase 1 imports (should raise DeprecationWarning)...")
result = subprocess.run(
    [
        sys.executable,
        "-W",
        "all",
        "-c",
        "from parquetframe.core import ParquetFrame",
    ],
    capture_output=True,
    text=True,
)

if "DeprecationWarning" in result.stderr and "deprecated" in result.stderr.lower():
    print("✓ Phase 1 imports raise DeprecationWarning with correct message")
else:
    print("✗ FAILED: Phase 1 imports did not raise DeprecationWarning")
    print("Output:")
    print(result.stderr)
    sys.exit(1)
# Test 3: FORMAT_HANDLERS should also be deprecated
print("\n[Test 3] Phase 1 FORMAT_HANDLERS (should raise DeprecationWarning)...")
result = subprocess.run(
    [
        sys.executable,
        "-W",
        "all",
        "-c",
        "from parquetframe.core import FORMAT_HANDLERS",
    ],
    capture_output=True,
    text=True,
)

if "DeprecationWarning" in result.stderr:
    print("✓ FORMAT_HANDLERS raises DeprecationWarning")
else:
    print("✗ FAILED: FORMAT_HANDLERS did not raise DeprecationWarning")
    print("Output:")
    print(result.stderr)
    sys.exit(1)
# Test 4: Invalid imports should raise ImportError
print("\n[Test 4] Invalid imports (should raise ImportError)...")
result = subprocess.run(
    [
        sys.executable,
        "-c",
        "from parquetframe.core import NonExistentClass",
    ],
    capture_output=True,
    text=True,
)

if result.returncode != 0 and (
    "cannot import name" in result.stderr or "has no attribute" in result.stderr
):
    print("✓ Invalid imports raise ImportError with correct message")
else:
    print("✗ FAILED: Invalid import did not raise proper ImportError")
    print("Output:")
    print(result.stderr)
    sys.exit(1)

print("\n" + "=" * 80)
print("All deprecation tests passed!")
print("=" * 80)
