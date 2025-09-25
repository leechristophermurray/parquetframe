# ParquetFrame Architecture

## Overview

ParquetFrame is evolving from a simple parquet file utility into a comprehensive, AI-powered data exploration and analysis platform. The architecture is designed around three core components:

1. **DataContext** - Unified abstraction for data sources
2. **LLM Agent** - Natural language to SQL conversion
3. **Interactive CLI** - Rich REPL interface

## DataContext Architecture

### Core Abstraction

The `DataContext` abstract base class provides a unified interface for working with different data sources:

```python
from parquetframe.datacontext import DataContextFactory

# Parquet data lake
context = DataContextFactory.create_from_path("./data_lake/")

# Database connection
context = DataContextFactory.create_from_db_uri("postgresql://user:pass@host/db")

await context.initialize()
schema = context.get_schema_as_text()  # For LLM consumption
result = await context.execute("SELECT * FROM table")
```

### Implementation Classes

#### ParquetDataContext
- **File Discovery**: Uses `pathlib.Path.rglob()` for recursive parquet file discovery
- **Schema Unification**: Automatically resolves schema differences across files
- **Query Engine**: DuckDB (preferred) or Polars for high-performance querying
- **Virtualization**: Presents multiple files as a single queryable table

#### DatabaseDataContext
- **Connection**: SQLAlchemy-based multi-database support
- **Introspection**: Lightweight schema discovery using Inspector pattern
- **Query Execution**: Direct SQL execution with pandas result formatting
- **Security**: Password masking and proper connection cleanup

### Factory Pattern

The `DataContextFactory` uses dependency injection to create appropriate contexts:

```python
# Automatically chooses implementation based on parameters
context = DataContextFactory.create_context(
    path="./data/",          # -> ParquetDataContext
    # db_uri="sqlite:///db"  # -> DatabaseDataContext
)
```

## LLM Integration

### Agent Architecture

The `LLMAgent` provides sophisticated natural language to SQL conversion:

```python
from parquetframe.ai import LLMAgent

agent = LLMAgent(model_name="llama3.2", max_retries=2)
result = await agent.generate_query("how many users are there?", data_context)
```

### Key Features

1. **Prompt Engineering**: Structured templates with schema injection
2. **Multi-Step Reasoning**: Table selection for complex queries
3. **Self-Correction**: Automatic retry with error feedback
4. **Few-Shot Learning**: Customizable examples for domain-specific queries

### Prompt System

The prompt system consists of several builders:

- `QueryPromptBuilder` - Main SQL generation prompts
- `MultiStepQueryPromptBuilder` - Table selection + focused generation
- `SelfCorrectionPromptBuilder` - Error correction prompts

Example prompt structure:
```
System: You are an expert SQL analyst...

Schema Context:
CREATE TABLE users (
  id INTEGER NOT NULL,
  name VARCHAR,
  email VARCHAR
);

Examples:
Question: "how many rows are there"
SQL: SELECT COUNT(*) FROM users;

Instructions: Provide ONLY the SQL query...

Question: "show me active users"
```

## Interactive CLI

### Session Management

The interactive CLI provides a rich REPL experience:

- **Context-Aware Prompts**: Shows data source type and AI status
- **Meta-Commands**: `\help`, `\list`, `\describe`, `\ai`, etc.
- **Session Persistence**: Save/load functionality with pickle
- **Query History**: Full logging of all interactions

### Command Structure

```
pframe:parquet🤖> \help         # Show all commands
pframe:database> \list          # List tables
pframe:parquet> \ai count users # Natural language query
pframe:parquet> SELECT * FROM data LIMIT 10;  # Direct SQL
```

### AI Integration

The CLI seamlessly integrates LLM capabilities:

1. User types `\ai <natural language question>`
2. LLM generates SQL query
3. Query is displayed for user approval
4. Upon approval, query is executed and results displayed
5. All interactions are logged for reproducibility

## Error Handling & UX

### Graceful Fallbacks

- **Missing Dependencies**: Clear installation instructions
- **Connection Failures**: Actionable error messages
- **Query Errors**: Automatic self-correction attempts
- **Schema Issues**: Warnings with promoted type information

### Rich UI Components

- **Progress Spinners**: For long-running operations
- **Formatted Tables**: Rich table display for query results
- **Color Coding**: Status indicators and syntax highlighting
- **Panels**: Organized information display

## Testing Strategy

### Coverage Areas

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: End-to-end workflows
3. **Mock Testing**: LLM interactions with deterministic responses
4. **Error Scenarios**: Connection failures, invalid queries, etc.

### Test Infrastructure

- **Fixtures**: Temporary parquet directories and databases
- **Async Support**: Full async/await testing with pytest-asyncio
- **Dependency Injection**: Easy mocking of external dependencies

## Performance Considerations

### Query Optimization

- **Lazy Evaluation**: Dask integration for large datasets
- **Predicate Pushdown**: Filter pushdown to file level
- **Schema Caching**: Avoid repeated metadata reads
- **Connection Pooling**: Efficient database connection reuse

### Memory Management

- **Streaming Results**: Limited result display (20 rows default)
- **Resource Cleanup**: Proper connection and file handle management
- **Context Managers**: Automatic resource cleanup

## Future Extensions

### Planned Features

1. **Cloud Storage**: S3/GCS/Azure integration
2. **Workflow Orchestration**: Multi-step data pipelines
3. **Real-time Monitoring**: Live query execution tracking
4. **Advanced Visualizations**: Integrated plotting capabilities

### Extension Points

- **Custom DataContexts**: Plugin system for new data sources
- **Model Providers**: Support for OpenAI, Anthropic, etc.
- **Output Formats**: JSON, CSV, Excel export options
- **Authentication**: OAuth, SSO integration

## Security & Privacy

### Data Protection

- **Local LLM**: Ollama ensures data stays on-premises
- **Connection Security**: Encrypted database connections
- **Credential Management**: Secure storage of connection strings
- **Audit Logging**: Full query and access logging

### Privacy Considerations

- **No Data Transmission**: Schema-only information sent to LLM
- **Local Processing**: All AI inference happens locally
- **User Control**: Explicit approval required for query execution
