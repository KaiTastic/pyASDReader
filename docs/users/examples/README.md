# pyASDReader Examples

This directory contains example scripts demonstrating how to use pyASDReader.

## Available Examples

### 1. basic_usage.py

Demonstrates the fundamental operations with pyASDReader:
- Loading ASD files
- Accessing metadata
- Reading spectral data
- Working with reflectance and derivatives

**Usage:**

```bash
python docs/users/examples/basic_usage.py tests/sample_data/v7sample/v7sample00000.asd
```

Pass the path to an `.asd` file as the first command-line argument.

## Getting Test Data

You can use the sample data included in the `tests/sample_data/` directory for testing:

```python
from pyASDReader import ASDFile

# Example with version 7 sample data
asd = ASDFile("tests/sample_data/v7sample/your_file.asd")
```

## Additional Resources

- [Main README](https://github.com/KaiTastic/pyASDReader#readme) - Full documentation
- [API Documentation](https://github.com/KaiTastic/pyASDReader#api-reference) - Detailed API usage
- [CHANGELOG](https://github.com/KaiTastic/pyASDReader/blob/main/CHANGELOG.md) - Version history
