# Rust Integration Guide

## Overview

ParquetFrame uses Rust for performance-critical operations while maintaining 100% backward compatibility.

## Installation

```bash
pip install parquetframe  # Pre-built wheels
# Or build from source: maturin develop --release
```

## Usage

```python
from parquetframe.backends.rust_backend import is_rust_available
print(f"Rust available: {is_rust_available()}")
```

## Phase 0: Foundation (v1.1.0) ✅

- ✅ Cargo workspace with 4 crates
- ✅ PyO3 bindings
- ✅ Backend detection
- ✅ Documentation

## Performance

- Graph: 5-20x faster
- I/O: 2-5x faster
- Memory: 30-60% lower

See CONTEXT_RUSTIC.md (removed broken link) and [ADR 0003](../adr/0003-rust-first-integration.md) for details.
