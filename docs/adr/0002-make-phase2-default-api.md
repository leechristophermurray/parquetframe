# ADR-0002: Make Phase 2 Multi-Engine API the Default

**Status**: Accepted

**Date**: 2025-10-18

**Deciders**: ParquetFrame Core Team

**Technical Story**: Removing v2 distinction and making Phase 2 the standard user experience

## Context and Problem Statement

ParquetFrame Phase 2 has been successfully implemented with a robust multi-engine architecture supporting pandas, Polars, and Dask. However, users must explicitly import `parquetframe.core_v2` to access these capabilities, creating a confusing developer experience:

1. **Namespace Confusion**: Having both `parquetframe` (Phase 1) and `parquetframe.core_v2` (Phase 2) creates uncertainty about which API to use
2. **Discovery Problem**: New users may not realize Phase 2 exists and miss out on performance improvements
3. **Migration Friction**: The "v2" suffix suggests experimental/unstable status despite Phase 2 being production-ready
4. **Documentation Complexity**: Maintaining parallel documentation for Phase 1 and Phase 2 increases cognitive load
5. **Future Burden**: Continuing to support dual APIs indefinitely increases maintenance overhead

Phase 2 is feature-complete, well-tested (146 passing tests), and provides significant improvements over Phase 1. It's time to make it the default experience.

## Decision Drivers

### User Experience Goals
- **Simplicity**: Single, clear import path (`import parquetframe`)
- **Discoverability**: New users get best-in-class experience by default
- **Performance**: Automatic multi-engine selection provides optimal performance
- **Progressive Enhancement**: Clear migration path for existing users

### Technical Requirements
- **Backward Compatibility**: Phase 1 API must remain accessible during deprecation period
- **Smooth Migration**: Existing code should continue working with deprecation warnings
- **Documentation Quality**: Clear breaking changes documentation and migration guides
- **Test Coverage**: Maintain >85% coverage throughout transition

### Project Standards
- **Semantic Versioning**: Breaking changes require major version bump
- **Conventional Commits**: All commits follow conventional commit format
- **Git Best Practices**: Feature branch workflow with descriptive commits

## Decision

We will make **Phase 2 multi-engine API the default** for all ParquetFrame imports while providing backward compatibility for Phase 1.

### Implementation Strategy

**1. Module Restructuring**
- Keep `src/parquetframe/core_v2/` as-is (implementation remains in separate module)
- Update `src/parquetframe/__init__.py` to import Phase 2 API by default
- Maintain Phase 1 API in `src/parquetframe/core_legacy.py` for backward compatibility
- Create `src/parquetframe/legacy/` submodule for explicit Phase 1 access

**2. Import Behavior**

```python
# New default behavior (Phase 2)
import parquetframe as pf
# Now provides: DataFrameProxy, read(), read_csv(), read_avro(), etc.
# Multi-engine support: pandas, Polars, Dask

# Explicit Phase 1 access (deprecated)
from parquetframe.legacy import ParquetFrame
# Triggers deprecation warning pointing to migration guide

# Direct Phase 2 access (still available)
from parquetframe.core_v2 import DataFrameProxy, read
# No changes needed for code already using core_v2
```

**3. Deprecation Strategy**

- **Version 1.0.0** (This release):
  - Phase 2 becomes default
  - Phase 1 available via `parquetframe.legacy` with deprecation warnings
  - Clear migration documentation provided

- **Version 1.x** (6-12 months):
  - Continue supporting Phase 1 API with deprecation warnings
  - Encourage migration through documentation and community outreach

- **Version 2.0.0** (Future):
  - Remove Phase 1 API entirely
  - `parquetframe.legacy` submodule removed

**4. Version Bump**

This is a **breaking change** requiring a major version bump:
- Current: `0.5.3`
- After this change: `1.0.0`

Justification: Making Phase 2 the default changes the return types and API surface for the primary import path, even though Phase 1 remains accessible via `legacy` submodule.

## Alternatives Considered

### Alternative A: Keep Both APIs Indefinitely (Rejected)

**Approach**: Maintain `parquetframe` (Phase 1) and `parquetframe.core_v2` (Phase 2) indefinitely.

**Pros**:
- No breaking changes
- Maximum backward compatibility
- Users choose when to migrate

**Cons**:
- Perpetual maintenance burden for two parallel APIs
- Confusing for new users
- Documentation complexity
- Prevents architecture evolution
- Phase 2 improvements don't benefit existing users

**Why Rejected**: Unsustainable long-term; prevents project evolution

### Alternative B: Gradual Default Switch with Flag (Rejected)

**Approach**: Add environment variable `PARQUETFRAME_DEFAULT_API=v1|v2` to control default behavior.

**Pros**:
- Users control migration timing
- No immediate breaking changes
- Gradual transition period

**Cons**:
- Adds configuration complexity
- Behavior differs based on environment
- Prolongs dual maintenance period
- Creates "hidden" breaking changes
- Testing matrix complexity

**Why Rejected**: Configuration-based behavior is confusing; better to be explicit

### Alternative C: Import-Based Selection (Rejected)

**Approach**: Different import paths determine API version:
```python
import parquetframe as pf        # Phase 1
import parquetframe.v2 as pf     # Phase 2
```

**Pros**:
- Clear version selection
- No breaking changes to existing code
- Explicit opt-in to new API

**Cons**:
- "v2" naming persists (doesn't solve core problem)
- New users may not discover v2
- Dual maintenance continues
- Naming becomes problematic when Phase 3 arrives

**Why Rejected**: Doesn't solve the namespace confusion; just renames it

### Alternative D: Make Phase 2 Default (Selected) ✅

**Approach**: Make Phase 2 the default import while providing backward compatibility via `legacy` submodule.

**Pros**:
- Clear, single import path for new users
- Best experience by default
- Legacy support during transition
- Standard deprecation workflow
- Enables future evolution
- Follows semantic versioning conventions

**Cons**:
- Breaking change requires major version bump
- Existing code needs updates (with clear migration path)
- Short-term documentation/support burden

**Why Selected**: Best long-term solution following industry best practices

## Consequences

### Positive Consequences

✅ **Improved User Experience**: Single, clear import path reduces confusion

✅ **Performance by Default**: New users automatically get multi-engine optimization

✅ **Simplified Documentation**: One primary API to document and teach

✅ **Future-Proof Architecture**: Enables continued evolution without namespace baggage

✅ **Industry Alignment**: Follows standard deprecation practices (Python, NumPy, pandas)

✅ **Marketing Clarity**: Version 1.0.0 signals production-ready, stable API

### Negative Consequences

❌ **Breaking Change**: Existing code using default imports will need updates

❌ **Migration Burden**: Users must update code or explicitly use `legacy` module

❌ **Documentation Update**: All docs need updates to reflect Phase 2 as default

❌ **Community Communication**: Requires clear messaging about changes and benefits

### Risk Mitigation

**Risk: User Adoption Resistance**

- *Mitigation*: Comprehensive migration guide with before/after examples
- *Mitigation*: Clear communication of Phase 2 performance benefits
- *Mitigation*: Deprecation warnings with helpful error messages
- *Mitigation*: 6-12 month transition period with legacy support

**Risk: Unexpected Breaking Changes**

- *Mitigation*: Comprehensive test suite ensures compatibility
- *Mitigation*: Breaking changes clearly documented in BREAKING_CHANGES.md
- *Mitigation*: Semantic versioning clearly signals breaking change (1.0.0)

**Risk: Documentation Gaps**

- *Mitigation*: Systematic documentation review and updates
- *Mitigation*: Migration guide with common patterns
- *Mitigation*: Updated examples throughout documentation

## Breaking Changes

### API Changes

| Aspect | Phase 1 (Old) | Phase 2 (New) |
|--------|---------------|---------------|
| **Main Class** | `ParquetFrame` | `DataFrameProxy` |
| **Backend Property** | `df.islazy` (bool) | `df.engine_name` (str) |
| **DataFrame Access** | `df.df` | `df.native` |
| **Backend Selection** | `islazy=True/False` | `engine="pandas"/"polars"/"dask"` |
| **Available Engines** | pandas, Dask | pandas, Polars, Dask |
| **Import Path** | `import parquetframe as pf` | `import parquetframe as pf` (same!) |

### Migration Path

**Before (Phase 1):**

```python
import parquetframe as pf

df = pf.read("data.csv", islazy=True)
if df.islazy:
    result = df.df.groupby("category").sum().compute()
else:
    result = df.df.groupby("category").sum()
```

**After (Phase 2):**
```python

import parquetframe as pf

df = pf.read("data.csv", engine="dask")
if df.engine_name == "dask":
    result = df.native.groupby("category").sum().compute()
else:
    result = df.native.groupby("category").sum()
```

**Or Using Legacy (Transition):**
```python
from parquetframe.legacy import ParquetFrame as pf
# Phase 1 code continues working (with deprecation warning)
```

## Implementation Checklist

- [x] Create feature branch: `refactor/make-phase2-default`
- [x] Create ADR documenting decision
- [x] Create BREAKING_CHANGES.md with migration guide
- [x] Restructure core module imports
- [x] Add deprecation warnings for Phase 1 API
- [x] Update internal imports throughout codebase
- [x] Update test suite for Phase 2 default
- [x] Update all documentation
- [x] Bump version to 1.0.0
- [x] Run quality checks (Black, Ruff, MyPy)
- [ ] Create pull request with breaking change notice

## Related Decisions

This ADR builds on:
- **ADR-0001**: Next-Generation Architecture for Phase 2
- Relates to future ADRs about Phase 1 API removal (v2.0.0)

## References

- [Phase 2 Migration Guide](../phase2/MIGRATION_GUIDE.md) - Existing Phase 1→2 migration guide
- [Semantic Versioning 2.0.0](https://semver.org/) - Version number conventions
- [Conventional Commits](https://www.conventionalcommits.org/) - Commit message format

## Success Metrics

This decision will be considered successful when:

1. **User Feedback**: Positive community response to simplified API
2. **Adoption Rate**: >50% of users migrate within 6 months
3. **Documentation**: All docs updated to reflect Phase 2 as default
4. **Test Coverage**: Maintained at >85% throughout transition
5. **Issue Reduction**: Fewer "which API should I use?" support requests

---

**Status**: Accepted

**Implementation**: In Progress (Branch: `refactor/make-phase2-default`)

**Next Review**: Post-implementation review after version 1.0.0 release
