#!/usr/bin/env python3
"""
Demo script for the interactive REPL.

Shows how to use the REPL for data exploration.
"""

import sys

print("=" * 70)
print("ParquetFrame Interactive REPL - Demo")
print("=" * 70)
print()

try:
    from parquetframe.cli.repl import start_repl

    print("Starting REPL...")
    print()
    print("Try these commands:")
    print("  pf[1]> import pandas as pd")
    print("  pf[2]> df = pd.DataFrame({'a': [1,2,3], 'b': [4,5,6]})")
    print("  pf[3]> %info df")
    print("  pf[4]> %whos")
    print("  pf[5]> exit")
    print()

    start_repl()

except ImportError as e:
    print(f"Error: {e}")
    print()
    print("Install dependencies:")
    print("  pip install prompt-toolkit rich pygments")
    sys.exit(1)
