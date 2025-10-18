# ADR-0001: Next-Generation Architecture for ParquetFrame Phase 2

**Status**: Proposed
**Date**: 2025-01-15
**Deciders**: ParquetFrame Core Team
**Technical Story**: Evolution from specialized DataFrame wrapper to next-generation data processing framework

## Context and Problem Statement

ParquetFrame has successfully completed Phase 1 with a robust foundation including multi-format support, advanced analytics, comprehensive graph processing, and permissions systems. However, the current architecture has limitations:

1. **Single Backend Paradigm**: Currently limited to pandas/Dask switching, missing opportunities for performance optimization with modern engines like Polars
2. **Format Constraints**: Limited to columnar formats, missing support for schema-rich formats like Apache Avro
3. **Data Modeling Gap**: No native support for entity-relationship modeling or persistent data structures
4. **Configuration Complexity**: Limited configuration management for advanced use cases
5. **Scalability Boundaries**: Architecture not optimized for next-generation DataFrame engines

Phase 2 aims to transform ParquetFrame into a next-generation data processing framework while maintaining 100% backward compatibility.

## Decision Drivers

### Performance Requirements
- **2-5x performance improvement** on medium-scale datasets (1GB-100GB)
- **Memory efficiency** through intelligent backend selection
- **Lazy evaluation** optimization via Polars integration
- **Distributed processing** scalability with enhanced Dask integration

### User Experience Goals
- **Zero-configuration performance** with intelligent defaults
- **Unified API** across all DataFrame engines
- **Backward compatibility** with existing ParquetFrame APIs
- **Progressive enhancement** allowing gradual adoption of new features

### Technical Objectives
- **Multi-engine abstraction** without external dependency overhead
- **Format extensibility** with pluggable I/O handlers
- **Entity-relationship modeling** for complex data workflows
- **Enterprise-grade configuration** management

## Considered Options

### Option A: External Abstraction Library (Rejected)
Use existing libraries like `ibis` or `dataframes-api-compat` for DataFrame abstraction.

**Pros**: Mature, battle-tested, external maintenance
**Cons**: Additional dependency, API constraints, limited customization

### Option B: Fork/Extend Existing Framework (Rejected)
Fork an existing multi-engine framework and extend it.

**Pros**: Head start on functionality
**Cons**: Maintenance burden, architectural mismatch, licensing complexity

### Option C: Custom Multi-Engine Core (Selected)
Build a custom, lightweight abstraction layer tailored for ParquetFrame's needs.

**Pros**: Full control, optimal performance, seamless integration, no external dependencies
**Cons**: Initial development overhead, ongoing maintenance responsibility

## Decision

We will implement **Option C: Custom Multi-Engine Core** with the following architectural components:

## Architecture Overview

### 1. Multi-Engine DataFrame Core

**Component**: Custom `DataFrameProxy` class with engine abstraction layer

**Design Principles**:
- **Engine Agnostic**: Unified API over pandas, Polars, and Dask
- **Zero Dependencies**: No external abstraction libraries
- **Intelligent Selection**: Automatic backend choice based on data characteristics
- **Method Translation**: Direct API mapping without performance overhead

**Key Classes**:
```python
class DataFrameProxy:
    """Unified DataFrame interface with intelligent backend selection."""

class EngineRegistry:
    """Registry for available DataFrame engines with capability discovery."""

class EngineHeuristics:
    """Intelligent engine selection based on data size, operations, and system resources."""
```

### 2. Engine Selection Strategy

**Two-Threshold System**:
- **Pandas**: `< 1GB` - Rich ecosystem, rapid prototyping, interactive analysis
- **Polars**: `1GB - 100GB` - High-performance single-machine processing with lazy evaluation
- **Dask**: `> 100GB` - Distributed processing for larger-than-memory datasets

**Selection Factors**:
- Dataset size (primary)
- Available system memory
- Operation complexity
- User preference (override)

**Configuration**:
```python
# Environment variable override
PARQUETFRAME_ENGINE=polars

# Programmatic configuration
pf.configure(
    pandas_threshold_mb=100,
    dask_threshold_mb=10000,
    default_engine="auto"
)
```

### 3. Apache Avro Integration

**Component**: High-performance Avro I/O with `fastavro` backend

**Features**:
- **Schema Inference**: Automatic Avro schema generation from DataFrame dtypes
- **Multi-Engine Support**: Read/write Avro across all DataFrame backends
- **Performance Focus**: 10x+ improvement over pure Python avro implementations
- **Schema Validation**: Robust error handling and schema compatibility checks

**API Design**:
```python
# Reading
df = pf.read("data.avro", engine="polars")  # Auto-detect Avro format

# Writing with schema inference
df.to_avro("output.avro", schema=None, codec="snappy")

# Explicit schema
df.to_avro("output.avro", schema=custom_avro_schema)
```

### 4. Entity-Graph Framework

**Component**: ORM-like system with decorators for data modeling

**Design Philosophy**:
- **Decorator-Driven**: `@entity` and `@rel` decorators for schema definition
- **Persistence Integration**: Seamless I/O with Parquet/Avro backends
- **Relationship Validation**: Foreign key integrity and orphan detection
- **Multi-Engine Compatibility**: Works across pandas, Polars, and Dask

**Example Usage**:
```python
@entity(storage_path="users/", primary_key="user_id")
@dataclass
class User:
    user_id: int
    name: str
    email: str

@entity(storage_path="orders/", primary_key="order_id")
@dataclass
class Order:
    order_id: int
    user_id: int
    amount: float

@rel(User, Order, foreign_key="user_id")
def user_orders(user: User) -> List[Order]:
    """User's order history with automatic relationship resolution."""
    pass
```

### 5. Configuration Architecture

**Component**: Hierarchical configuration system with multiple sources

**Configuration Precedence** (highest to lowest):
1. Function arguments
2. Environment variables (`PARQUETFRAME_*`)
3. Configuration file (`pyproject.toml` `[tool.parquetframe]`)
4. System defaults

**Configuration Categories**:
- **Engine Selection**: Thresholds, defaults, override behavior
- **I/O Settings**: Compression, partitioning, format preferences
- **Performance**: Memory limits, parallelism, caching
- **Logging**: Verbosity, structured output, progress indicators

### 6. User Experience Enhancements

**Progress Indicators**: Visual feedback for long-running operations
**Memory Monitoring**: Automatic warnings for memory-intensive operations
**Backend Explanation**: Transparent reporting of engine selection decisions
**Debug Mode**: Detailed operation tracing and performance profiling
**Enhanced CLI**: Rich terminal output with Phase 2 feature integration

## Implementation Strategy

### Phase 2.1: Multi-Engine DataFrame Core (4-5 weeks)
1. **Week 1-2**: DataFrameProxy implementation and backend detection
2. **Week 2-3**: Engine selection factory and operation mapping
3. **Week 4-5**: Polars integration with lazy evaluation optimization

### Phase 2.2: Apache Avro Integration (1-2 weeks)
1. **Week 1**: Avro reader/writer with schema inference
2. **Week 1-2**: Multi-engine integration and performance testing

### Phase 2.3: Entity-Graph Framework (3-4 weeks)
1. **Week 1-2**: `@entity` decorator and persistence methods
2. **Week 2-3**: `@rel` decorator and relationship validation
3. **Week 3-4**: Integration examples and performance optimization

### Phase 2.4-2.6: Configuration, Testing, Documentation (4-5 weeks)
1. **Weeks 1-2**: Configuration system and UX enhancements
2. **Weeks 2-3**: Comprehensive testing and quality assurance
3. **Weeks 4-5**: Documentation and migration guides

## Consequences

### Positive Consequences

✅ **Performance Excellence**: 2-5x improvements through intelligent engine selection
✅ **Developer Productivity**: Unified API reduces cognitive overhead
✅ **Future-Proof Architecture**: Extensible design accommodates new DataFrame engines
✅ **Backward Compatibility**: Zero breaking changes for existing users
✅ **Enterprise Readiness**: Comprehensive configuration and monitoring capabilities

### Negative Consequences

❌ **Implementation Complexity**: Custom abstraction layer requires significant development effort
❌ **Maintenance Responsibility**: Ongoing burden of maintaining engine compatibility
❌ **Testing Complexity**: Ensuring correctness across multiple engine backends
❌ **Learning Curve**: New concepts (entity-graph, multi-engine) require user education

### Risk Mitigation Strategies

**Performance Regression Risk**: Comprehensive benchmarking suite with regression detection
**Compatibility Risk**: Extensive cross-engine testing and property-based validation
**Maintenance Risk**: Modular architecture enabling incremental updates
**User Adoption Risk**: Progressive enhancement with gradual feature introduction

## Compliance and Constraints

### Backward Compatibility Requirements
- **API Preservation**: All existing ParquetFrame methods must continue to work
- **Behavior Consistency**: Default behavior unchanged unless explicitly configured
- **Migration Path**: Clear upgrade path with minimal required changes

### Performance Requirements
- **Benchmark Targets**: 2-5x improvement on medium-scale datasets
- **Memory Efficiency**: Intelligent backend selection minimizes memory usage
- **Startup Performance**: No significant overhead in import/initialization time

### Quality Standards
- **Test Coverage**: ≥85% coverage across all Phase 2 modules
- **Type Safety**: Full mypy compliance in strict mode
- **Code Quality**: Ruff/Black formatting with comprehensive linting
- **Documentation**: Complete API reference with examples and tutorials

## Related Decisions

This ADR relates to and will be followed by:

- **ADR-0002**: Engine Selection Heuristics Algorithm
- **ADR-0003**: Entity-Graph Persistence Format Specification
- **ADR-0004**: Configuration Schema and Precedence Rules
- **ADR-0005**: Avro Schema Inference Algorithm

## References

- [Apache Arrow Specification](https://arrow.apache.org/docs/format/Columnar.html) - Columnar format standards
- [Apache Avro Specification](https://avro.apache.org/docs/current/spec.html) - Schema-rich serialization format
- [Polars User Guide](https://pola-rs.github.io/polars-book/) - Lazy evaluation patterns
- [Dask DataFrame Documentation](https://docs.dask.org/en/latest/dataframe.html) - Distributed processing patterns

---

**Status**: Proposed
**Next Review**: Implementation planning for Phase 2.1 Multi-Engine Core
**Implementation Target**: Q1 2025
