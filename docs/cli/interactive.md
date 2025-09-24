# Interactive Mode

> Use ParquetFrame's interactive CLI for exploratory data analysis.

## Interactive CLI

The interactive mode provides a REPL-like experience for data exploration and analysis.

## Starting Interactive Mode

Launch interactive mode with your data:

```bash
pframe interactive data.parquet
```

## Available Commands

In interactive mode, you can:
- Explore data structure
- Run queries
- Perform transformations
- Save results

## Session Management

- Save your session
- Load previous sessions
- Export command history

## Summary

Interactive mode makes exploratory data analysis fast and intuitive from the command line.

## Examples

```bash
# Start interactive session
pframe interactive sales_data.parquet

# Interactive commands (within the session)
> head 10
> describe
> filter "sales > 1000"
> groupby region sum sales
> save filtered_data.parquet
```

## Further Reading

- [CLI Overview](index.md)
- [Basic Commands](commands.md)
- [Batch Processing](batch.md)