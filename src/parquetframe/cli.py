"""
Command Line Interface for ParquetFrame.

This module provides a powerful CLI for interacting with parquet files,
including batch processing and interactive modes.
"""

import code
import sys
from pathlib import Path
from typing import Optional

try:
    import click
    from rich.console import Console
    from rich.table import Table
    from rich.text import Text
except ImportError as e:
    print(f"CLI dependencies not installed. Install with: pip install parquetframe[cli]")
    print(f"Missing: {e.name}")
    sys.exit(1)

from .core import ParquetFrame

try:
    from .benchmark import run_comprehensive_benchmark, PerformanceBenchmark
    BENCHMARK_AVAILABLE = True
except ImportError:
    BENCHMARK_AVAILABLE = False

# Global console for rich output
console = Console()


@click.group()
@click.version_option()
def main():
    """
    ParquetFrame CLI - A powerful tool for working with parquet files.
    
    Automatically switches between pandas and Dask based on file size.
    Provides both batch processing and interactive modes.
    
    Examples:
        pframe run data.parquet --query "age > 30" --head 10
        pframe interactive data.parquet
        pframe info data.parquet
    """
    pass


@main.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option(
    "--query", "-q", 
    help="Pandas/Dask query to filter data (e.g., 'age > 30')"
)
@click.option(
    "--columns", "-c", 
    help="Comma-separated columns to select (e.g., 'name,age,city')"
)
@click.option(
    "--head", "-h", 
    type=int, 
    help="Display first N rows"
)
@click.option(
    "--tail", "-t", 
    type=int, 
    help="Display last N rows"
)
@click.option(
    "--sample", "-s", 
    type=int, 
    help="Display N random sample rows"
)
@click.option(
    "--output", "-o", 
    type=click.Path(), 
    help="Save result to output parquet file"
)
@click.option(
    "--save-script", "-S", 
    type=click.Path(), 
    help="Save session as Python script"
)
@click.option(
    "--threshold", 
    type=float, 
    default=10, 
    help="File size threshold in MB for Dask vs pandas (default: 10)"
)
@click.option(
    "--force-dask", 
    is_flag=True, 
    help="Force use of Dask backend"
)
@click.option(
    "--force-pandas", 
    is_flag=True, 
    help="Force use of pandas backend"
)
@click.option(
    "--describe", 
    is_flag=True, 
    help="Show statistical description of data"
)
@click.option(
    "--info", 
    is_flag=True, 
    help="Show data info (dtypes, null counts, etc.)"
)
def run(
    filepath, query, columns, head, tail, sample, output, save_script, 
    threshold, force_dask, force_pandas, describe, info
):
    """
    Run operations on a parquet file in batch mode.
    
    This command processes a parquet file with the specified operations
    and optionally saves the result and/or generates a Python script.
    
    Examples:
        pframe run data.parquet --query "age >= 21" --columns "name,email" --head 5
        pframe run large.parquet --force-dask --describe
        pframe run data.parquet --output filtered.parquet --save-script process.py
    """
    # Determine backend selection
    islazy = None
    if force_dask and force_pandas:
        click.echo("Error: Cannot use both --force-dask and --force-pandas", err=True)
        sys.exit(1)
    elif force_dask:
        islazy = True
    elif force_pandas:
        islazy = False

    # Enable session tracking for script generation
    ParquetFrame._current_session_tracking = save_script is not None

    try:
        # Read the file
        console.print(f"[bold blue]Reading file:[/bold blue] {filepath}")
        pf = ParquetFrame.read(filepath, threshold_mb=threshold, islazy=islazy)
        
        # Apply query filter
        if query:
            console.print(f"[bold yellow]Applying query:[/bold yellow] {query}")
            pf = pf.query(query)
            
        # Select columns
        if columns:
            cols = [col.strip() for col in columns.split(",")]
            console.print(f"[bold yellow]Selecting columns:[/bold yellow] {', '.join(cols)}")
            pf = pf[cols]
            
        # Show info if requested
        if info:
            console.print("\n[bold green]Data Info:[/bold green]")
            if pf.islazy:
                # For Dask, show basic info
                console.print(f"Backend: Dask DataFrame")
                console.print(f"Columns: {list(pf.columns)}")
                console.print(f"Partitions: {pf._df.npartitions}")
            else:
                # For pandas, show detailed info
                pf.info()
                
        # Show description if requested
        if describe:
            console.print("\n[bold green]Statistical Description:[/bold green]")
            desc = pf.describe()
            if pf.islazy:
                desc = desc.compute()
            _display_dataframe_as_table(desc, "Statistical Description")
            
        # Display data samples
        if head:
            console.print(f"\n[bold green]First {head} rows:[/bold green]")
            sample_data = pf.head(head)
            # Check if sample_data is a ParquetFrame or DataFrame and handle accordingly
            if hasattr(sample_data, 'islazy') and sample_data.islazy:
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, '_df') and hasattr(sample_data._df, 'compute'):
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, 'compute'):
                sample_data = sample_data.compute()
            elif hasattr(sample_data, '_df'):
                sample_data = sample_data._df
            _display_dataframe_as_table(sample_data, f"First {head} Rows")
            
        elif tail:
            console.print(f"\n[bold green]Last {tail} rows:[/bold green]")
            sample_data = pf.tail(tail)
            if hasattr(sample_data, 'islazy') and sample_data.islazy:
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, '_df') and hasattr(sample_data._df, 'compute'):
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, 'compute'):
                sample_data = sample_data.compute()
            elif hasattr(sample_data, '_df'):
                sample_data = sample_data._df
            _display_dataframe_as_table(sample_data, f"Last {tail} Rows")
            
        elif sample:
            console.print(f"\n[bold green]Random sample of {sample} rows:[/bold green]")
            sample_data = pf.sample(sample)
            if hasattr(sample_data, 'islazy') and sample_data.islazy:
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, '_df') and hasattr(sample_data._df, 'compute'):
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, 'compute'):
                sample_data = sample_data.compute()
            elif hasattr(sample_data, '_df'):
                sample_data = sample_data._df
            _display_dataframe_as_table(sample_data, f"Random Sample ({sample} rows)")
            
        # Default: show first 5 rows if no specific display was requested
        elif not info and not describe:
            console.print("\n[bold green]Preview (first 5 rows):[/bold green]")
            sample_data = pf.head(5)
            if hasattr(sample_data, 'islazy') and sample_data.islazy:
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, '_df') and hasattr(sample_data._df, 'compute'):
                sample_data = sample_data._df.compute()
            elif hasattr(sample_data, 'compute'):
                sample_data = sample_data.compute()
            elif hasattr(sample_data, '_df'):
                sample_data = sample_data._df
            _display_dataframe_as_table(sample_data, "Preview")
            
        # Save output if requested
        if output:
            console.print(f"\n[bold blue]Saving to:[/bold blue] {output}")
            pf.save(output, save_script=save_script)
        elif save_script and pf._track_history:
            # Save script even if no output file
            pf._save_history_script(save_script)
            
        console.print("\n[bold green]✓ Operation completed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@main.command()
@click.argument("filepath", type=click.Path(exists=True), required=False)
@click.option(
    "--threshold", 
    type=float, 
    default=10, 
    help="File size threshold in MB for Dask vs pandas (default: 10)"
)
def interactive(filepath, threshold):
    """
    Start an interactive Python session with ParquetFrame.
    
    Launches a Python REPL with a ParquetFrame object available as 'pf'.
    If a file is provided, it's automatically loaded.
    
    Examples:
        pframe interactive
        pframe interactive data.parquet
    """
    # Enable session tracking for interactive mode
    ParquetFrame._current_session_tracking = True
    
    # Create ParquetFrame instance with history tracking
    pf = ParquetFrame(track_history=True)
    
    # Load file if provided
    if filepath:
        console.print(f"[bold blue]Loading file:[/bold blue] {filepath}")
        try:
            pf = ParquetFrame.read(filepath, threshold_mb=threshold)
            pf._track_history = True  # Enable history tracking after read
            pf._history = [f"pf = ParquetFrame.read('{filepath}', threshold_mb={threshold})"]
        except Exception as e:
            console.print(f"[bold red]Error loading file:[/bold red] {e}")
            console.print("Starting with empty ParquetFrame...")
    
    # Setup interactive context
    context = {
        'pf': pf,
        'pd': __import__('pandas'),
        'dd': __import__('dask.dataframe'),
        'ParquetFrame': ParquetFrame,
        'console': console,
    }
    
    # Create banner
    banner_text = Text()
    banner_text.append("🚀 Welcome to ParquetFrame Interactive Mode!\n\n", style="bold blue")
    banner_text.append("Available variables:\n", style="bold")
    banner_text.append("  • pf", style="cyan")
    banner_text.append(" - Your ParquetFrame instance\n")
    banner_text.append("  • pd", style="cyan") 
    banner_text.append(" - pandas module\n")
    banner_text.append("  • dd", style="cyan")
    banner_text.append(" - dask.dataframe module\n")
    banner_text.append("  • console", style="cyan")
    banner_text.append(" - rich console for pretty printing\n\n")
    banner_text.append("Tips:\n", style="bold")
    banner_text.append("  • Use pf.get_history() to see command history\n")
    banner_text.append("  • Use pf.save('output', save_script='session.py') to save work\n")
    banner_text.append("  • Use exit() or Ctrl+D to quit\n\n")
    
    console.print(banner_text)
    
    # Additional setup for better REPL experience
    import readline
    import atexit
    
    # History file for readline
    history_file = Path.home() / ".parquetframe_history"
    try:
        readline.read_history_file(str(history_file))
    except FileNotFoundError:
        pass
    atexit.register(readline.write_history_file, str(history_file))
    
    # Start interactive session
    try:
        code.interact(banner="", local=context)
    except (EOFError, KeyboardInterrupt):
        console.print("\n[bold blue]Goodbye![/bold blue]")


@main.command()
@click.argument("filepath", type=click.Path(exists=True))
def info(filepath):
    """
    Display detailed information about a parquet file.
    
    Shows file size, column information, data types, and basic statistics
    without loading the entire file into memory.
    
    Examples:
        pframe info data.parquet
        pframe info large_dataset.pqt
    """
    try:
        # Get file info
        file_path = Path(filepath)
        file_size = file_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        console.print(f"\n[bold blue]File Information:[/bold blue] {filepath}")
        
        # Create info table
        info_table = Table(title="File Details")
        info_table.add_column("Property", style="cyan", no_wrap=True)
        info_table.add_column("Value", style="white")
        
        info_table.add_row("File Path", str(file_path.absolute()))
        info_table.add_row("File Size", f"{file_size:,} bytes ({file_size_mb:.2f} MB)")
        
        # Determine recommended backend
        backend = "Dask (lazy)" if file_size_mb >= 10 else "pandas (eager)"
        info_table.add_row("Recommended Backend", backend)
        
        console.print(info_table)
        
        # Try to read metadata without loading full file
        try:
            import pyarrow.parquet as pq
            parquet_file = pq.ParquetFile(filepath)
            
            console.print(f"\n[bold green]Parquet Schema:[/bold green]")
            schema_table = Table()
            schema_table.add_column("Column", style="cyan")
            schema_table.add_column("Type", style="yellow")
            schema_table.add_column("Nullable", style="white")
            
            for i, field in enumerate(parquet_file.schema.to_arrow_schema()):
                nullable = "Yes" if field.nullable else "No"
                schema_table.add_row(field.name, str(field.type), nullable)
                
            console.print(schema_table)
            
            # Additional parquet metadata
            console.print(f"\n[bold green]Parquet Metadata:[/bold green]")
            meta_table = Table()
            meta_table.add_column("Property", style="cyan")
            meta_table.add_column("Value", style="white")
            
            meta_table.add_row("Row Groups", str(parquet_file.metadata.num_row_groups))
            meta_table.add_row("Total Rows", f"{parquet_file.metadata.num_rows:,}")
            meta_table.add_row("Total Columns", str(parquet_file.metadata.num_columns))
            
            console.print(meta_table)
            
        except ImportError:
            console.print("[yellow]Install pyarrow for detailed schema information[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Could not read parquet metadata: {e}[/yellow]")
            
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)


@main.command()
@click.option(
    "--output", "-o",
    type=click.Path(),
    help="Save benchmark results to JSON file"
)
@click.option(
    "--quiet", "-q",
    is_flag=True,
    help="Run benchmark in quiet mode (less output)"
)
@click.option(
    "--operations",
    help="Comma-separated list of operations to benchmark (groupby,filter,sort,aggregation,join)"
)
@click.option(
    "--file-sizes",
    help="Comma-separated list of test file sizes in rows (e.g., '1000,10000,100000')"
)
def benchmark(output, quiet, operations, file_sizes):
    """
    Run performance benchmarks for ParquetFrame operations.
    
    This command runs comprehensive performance tests comparing pandas
    and Dask backends across different file sizes and operations.
    
    Examples:
        pframe benchmark
        pframe benchmark --output results.json --quiet
        pframe benchmark --operations "groupby,filter,sort"
        pframe benchmark --file-sizes "1000,50000,200000"
    """
    if not BENCHMARK_AVAILABLE:
        console.print("[bold red]Error:[/bold red] Benchmark functionality requires additional dependencies.")
        console.print("Please install with: pip install parquetframe[cli] psutil")
        sys.exit(1)
    
    # Parse operations if provided
    ops_list = None
    if operations:
        ops_list = [op.strip() for op in operations.split(",")]
        valid_ops = {"groupby", "filter", "sort", "aggregation", "join"}
        invalid_ops = set(ops_list) - valid_ops
        if invalid_ops:
            console.print(f"[bold red]Error:[/bold red] Invalid operations: {', '.join(invalid_ops)}")
            console.print(f"Valid operations: {', '.join(sorted(valid_ops))}")
            sys.exit(1)
    
    # Parse file sizes if provided
    file_sizes_list = None
    if file_sizes:
        try:
            sizes = [int(size.strip()) for size in file_sizes.split(",")]
            file_sizes_list = [(size, f"{size:,} rows") for size in sizes]
        except ValueError:
            console.print("[bold red]Error:[/bold red] Invalid file sizes. Use comma-separated integers.")
            sys.exit(1)
    
    try:
        verbose = not quiet
        
        if verbose:
            console.print("🔥 [bold green]Starting ParquetFrame Performance Benchmark[/bold green]")
            console.print("This may take several minutes...\n")
        
        # Create custom benchmark if needed
        if ops_list or file_sizes_list:
            benchmark_obj = PerformanceBenchmark(verbose=verbose)
            results = []
            
            # Run read operations benchmark
            if file_sizes_list:
                read_results = benchmark_obj.benchmark_read_operations(file_sizes_list)
                results.extend(read_results)
            else:
                read_results = benchmark_obj.benchmark_read_operations()
                results.extend(read_results)
            
            # Run operations benchmark
            if ops_list:
                op_results = benchmark_obj.benchmark_operations(ops_list)
                results.extend(op_results)
            else:
                op_results = benchmark_obj.benchmark_operations()
                results.extend(op_results)
            
            # Run threshold analysis
            threshold_results = benchmark_obj.benchmark_threshold_sensitivity()
            results.extend(threshold_results)
            
            if verbose:
                benchmark_obj.generate_report()
            
            # Compile custom results
            all_results = {
                'read_operations': [r.__dict__ for r in read_results],
                'data_operations': [r.__dict__ for r in op_results],
                'threshold_analysis': [r.__dict__ for r in threshold_results],
                'summary': {
                    'total_benchmarks': len(results),
                    'successful_benchmarks': sum(1 for r in results if r.success),
                    'average_execution_time': sum(r.execution_time for r in results) / len(results) if results else 0,
                    'average_memory_usage': sum(r.memory_peak for r in results) / len(results) if results else 0
                }
            }
        else:
            # Run comprehensive benchmark
            all_results = run_comprehensive_benchmark(output_file=None, verbose=verbose)
        
        # Save results if requested
        if output:
            import json
            with open(output, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)
            if verbose:
                console.print(f"\n📊 [bold blue]Results saved to:[/bold blue] {output}")
        
        if verbose:
            console.print("\n[bold green]✓ Benchmark completed successfully![/bold green]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Benchmark interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Error during benchmark:[/bold red] {e}")
        if verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


def _display_dataframe_as_table(df, title="DataFrame"):
    """Display a pandas DataFrame as a rich table."""
    if df.empty:
        console.print(f"[yellow]{title} is empty[/yellow]")
        return
        
    # Limit display size for readability
    display_df = df.head(20) if len(df) > 20 else df
    
    table = Table(title=title, show_header=True, header_style="bold blue")
    
    # Add index column if it's not the default range index
    if not isinstance(df.index, __import__('pandas').RangeIndex) or df.index.name:
        table.add_column("Index", style="dim")
        
    # Add data columns
    for col in display_df.columns:
        table.add_column(str(col), overflow="fold")
        
    # Add rows
    for idx, row in display_df.iterrows():
        row_data = []
        
        # Add index value if needed
        if not isinstance(df.index, __import__('pandas').RangeIndex) or df.index.name:
            row_data.append(str(idx))
            
        # Add column values
        for val in row:
            if __import__('pandas').isna(val):
                row_data.append("[dim]null[/dim]")
            else:
                # Truncate long values
                str_val = str(val)
                if len(str_val) > 50:
                    str_val = str_val[:47] + "..."
                row_data.append(str_val)
                
        table.add_row(*row_data)
        
    console.print(table)
    
    if len(df) > 20:
        console.print(f"[dim]... showing first 20 of {len(df)} rows[/dim]")


if __name__ == "__main__":
    main()