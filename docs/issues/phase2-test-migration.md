# Phase 2 API Test Migration Tracking

## Overview
Tests need migration from Phase 1 (legacy ParquetFrame) to Phase 2 (DataFrameProxy) API.

## Skipped Test Files
- tests/test_sql_matrix.py (87 tests)
- tests/test_sql_multiformat.py (15 tests)
- tests/test_sql_regression.py (14 tests)
- tests/test_ai_sql_integration.py (29 tests)
- tests/test_coverage_boost.py (8 tests)

## Migration Options
1. Expose .sql() method on DataFrameProxy
2. Update tests to import from parquetframe.sql directly
3. Update tests to use parquetframe.legacy for SQL operations

## Unsupported Formats in Phase 2
Phase 2 reader doesn't support: .json, .jsonl, .orc
Options: Add format support or skip format-specific tests

## API Changes Needed
- Expose create_empty() in Phase 2 __init__.py
- Define pf alias
- Ensure .sql() method availability on DataFrameProxy
