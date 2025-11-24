# Knowlogy Libraries

ParquetFrame's Knowlogy system provides curated knowledge libraries for various domains.

## Available Libraries

### Statistics
Core statistical concepts including descriptive stats, probability, inferential statistics, and regression.

**Concepts**: Mean, Variance, Standard Deviation, Z-Score, t-test, Chi-squared, Correlation, and more.

```python
from parquetframe import knowlogy

# Load statistics library
knowlogy.load_library("statistics")

# Search for concepts
concepts = knowlogy.search("variance")
print(concepts[0].description)

# Get formula
formula = knowlogy.get_formula("Standard Deviation")
print(formula.latex)  # s = \sqrt{s^2}
```

### Physics
Classical physics concepts, laws, and fundamental formulas.

**Concepts**: Newton's Laws, Kinetic Energy, Potential Energy, Momentum, E=mc².

```python
knowlogy.load_library("physics")

# Search
concepts = knowlogy.search("Newton")
formula = knowlogy.get_formula("Kinetic Energy")
print(formula.latex)  # KE = \frac{1}{2}mv^2
```

### Finance
Financial analysis, valuation, and portfolio management concepts.

**Concepts**: NPV, ROI, Sharpe Ratio, CAPM, Black-Scholes.

```python
knowlogy.load_library("finance")

# Get financial formulas
npv = knowlogy.get_formula("Net Present Value")
sharpe = knowlogy.get_formula("Sharpe Ratio")
```

## RAG Integration

Knowlogy provides structured, verifiable context for RAG systems:

```python
# Get context for LLM
context = knowlogy.get_context("How do I calculate standard deviation?")

# Context includes:
# - Concept definitions
# - LaTeX formulas
# - Related concepts
```

## Library Management

```python
# List available libraries
libs = knowlogy.list_libraries()
print(libs)
# {'statistics': '...', 'physics': '...', 'finance': '...'}

# Check if loaded
from parquetframe.knowlogy.library import LibraryManager
is_loaded = LibraryManager.is_library_loaded("statistics")
```
