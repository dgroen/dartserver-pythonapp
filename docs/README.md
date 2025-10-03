# Documentation

This directory contains all project documentation.

## Structure

- `source/` - Documentation source files (for Sphinx or other documentation generators)
- `build/` - Generated documentation output (HTML, PDF, etc.)

## Building Documentation

To build the documentation, run:

```bash
make docs
```

or with tox:

```bash
tox -e docs
```

The generated documentation will be available in `docs/build/html/`.

## Documentation Files

All markdown documentation files should be stored in this directory or its subdirectories.