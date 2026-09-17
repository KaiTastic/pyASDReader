---
title: pyASDReader
description: Read and parse ASD binary spectral files with Python.
---

# pyASDReader

**Read ASD (Analytical Spectral Devices) binary spectral files with Python.**

```{toctree}
:maxdepth: 3

developers/readme
maintainers/index
```

pyASDReader is a lightweight library for extracting spectral measurements, wavelength arrays, metadata, reference data, and calibration information from ASD files. It is designed for data workflows involving FieldSpec, LabSpec, TerraSpec, HandHeld, AgriSpec, and related instruments.

[![PyPI version](https://img.shields.io/pypi/v/pyASDReader?style=flat-square)](https://pypi.org/project/pyASDReader/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyASDReader?style=flat-square)](https://pypi.org/project/pyASDReader/)
[![Tests](https://github.com/KaiTastic/pyASDReader/actions/workflows/python-package.yml/badge.svg?branch=main&label=tests&style=flat-square)](https://github.com/KaiTastic/pyASDReader/actions)
[![License](https://img.shields.io/github/license/KaiTastic/pyASDReader?style=flat-square)](https://github.com/KaiTastic/pyASDReader/blob/main/LICENSE)

## At A Glance

- Supports ASD file format versions **v1 through v8**.
- Exposes wavelength, reflectance, radiance, irradiance, reference, metadata, and calibration data.
- Provides derived spectral values such as first and second derivatives and `log(1/R)` transformations.
- Requires Python **3.8 or newer** and NumPy **1.20 or newer**.
- Distributed under the [MIT License](https://github.com/KaiTastic/pyASDReader/blob/main/LICENSE).

## Installation

Install the latest stable release from PyPI:

```bash
python -m pip install pyASDReader
```

For development, clone the repository and install its development extras:

```bash
git clone https://github.com/KaiTastic/pyASDReader.git
cd pyASDReader
python -m pip install -e ".[dev]"
```

## Quick Start

Pass an `.asd` path to `ASDFile`. The file is read during initialization and the parsed values are available as attributes:

```python
from pyASDReader import ASDFile

asd = ASDFile("path/to/your/spectrum.asd")

print(f"ASD version: {asd.asdFileVersion}")
print(f"Channels: {len(asd.wavelengths)}")
print(f"Wavelength range: {asd.wavelengths[0]}-{asd.wavelengths[-1]} nm")

wavelengths = asd.wavelengths
reflectance = asd.reflectance
metadata = asd.metadata
```

You can also create an object first and load a file later:

```python
asd = ASDFile()
success = asd.read("path/to/your/spectrum.asd")
if not success:
	raise RuntimeError("The ASD file could not be read")
```

## Reading And Plotting A Spectrum

The parsed wavelength and measurement arrays can be passed directly to NumPy- or Matplotlib-based workflows:

```python
import matplotlib.pyplot as plt
from pyASDReader import ASDFile

asd = ASDFile("sample_spectrum.asd")

plt.plot(asd.wavelengths, asd.reflectance)
plt.xlabel("Wavelength (nm)")
plt.ylabel("Reflectance")
plt.title("ASD spectrum")
plt.grid(True)
plt.show()
```

## Available Data

The main `ASDFile` object exposes the following commonly used values:

| Attribute | Description |
| --- | --- |
| `wavelengths` | Wavelength values in nanometers |
| `reflectance` | Reflectance spectrum |
| `absoluteReflectance` | Absolute reflectance spectrum |
| `radiance` | Radiance data |
| `irradiance` | Irradiance data |
| `reflectance1stDeriv` | First derivative of reflectance |
| `reflectance2ndDeriv` | Second derivative of reflectance |
| `log1R` | `log(1/R)` transformation |
| `log1R1stDeriv` | First derivative of `log(1/R)` |
| `log1R2ndDeriv` | Second derivative of `log(1/R)` |
| `metadata` | Parsed file and instrument metadata |
| `asdFileVersion` | Detected ASD file format version |

The parser also reads reference, classifier, dependent-variable, calibration, audit-log, and signature sections when those sections are present in the file version being processed.

## Format And Instrument Coverage

The reader is intended for ASD files produced by instruments in these families:

| Instrument family | Examples |
| --- | --- |
| FieldSpec | 4 Hi-Res NG, 4 Hi-Res, 4 Standard-Res, 4 Wide-Res |
| LabSpec | 4 Bench, 4 Hi-Res, 4 Standard-Res |
| TerraSpec | 4 Hi-Res, 4 Standard-Res |
| HandHeld | 2 Pro, 2 |
| Other ASD instruments | AgriSpec and compatible ASD devices |

Actual fields depend on the instrument model and the ASD file version. Treat optional sections and metadata as data-dependent when building a general-purpose pipeline.

## Documentation Map

### For Users

- [API and implementation overview](https://github.com/KaiTastic/pyASDReader#api-reference) - Core class, properties, and methods.
- [Examples](https://github.com/KaiTastic/pyASDReader/tree/main/examples) - Small runnable usage examples.
- [Changelog](https://github.com/KaiTastic/pyASDReader/blob/main/CHANGELOG.md) - Release history and behavior changes.

### For Contributors

- [Contributing guide](https://github.com/KaiTastic/pyASDReader/blob/main/CONTRIBUTING.md) - Local setup, tests, and contribution workflow.
- [Architecture notes](developers/readme.md) - Class design documentation.
- [Version management](https://github.com/KaiTastic/pyASDReader/blob/main/VERSION_MANAGEMENT.md) - Release and versioning workflow.

### For Release Maintainers

These documents describe the release pipeline and are grouped under `docs/maintainers/` so release procedures remain separate from user-facing documentation.

- [CI/CD workflows](maintainers/CI_CD_WORKFLOWS.md) - Test, build, TestPyPI, and PyPI workflows.
- [Release examples](maintainers/RELEASE_EXAMPLES.md) - Normal, hotfix, pre-release, and manual release scenarios.
- [GitHub Environment setup](maintainers/GITHUB_ENVIRONMENT_SETUP.md) - Production deployment protection and approval rules.
- [Trusted Publishing setup](maintainers/TRUSTED_PUBLISHING_SETUP.md) - Token-less PyPI publishing with GitHub OIDC.
- [Trusted Publishing troubleshooting](maintainers/TROUBLESHOOTING_TRUSTED_PUBLISHING.md) - Diagnostic checklist and common fixes.
- [API token fallback](maintainers/FALLBACK_API_TOKEN_SETUP.md) - Backup authentication method when OIDC is unavailable.
- [Version rollback](maintainers/VERSION_ROLLBACK.md) - Yank, hotfix, and emergency rollback procedures.
- [Trusted Publishing implementation summary](maintainers/TRUSTED_PUBLISHING_IMPLEMENTATION_SUMMARY.md) - Historical implementation record and verification checklist.
- [Version management improvements](maintainers/IMPROVEMENTS_2025-10-07.md) - Historical notes about release-system improvements.

## Development

Run the test suite from the repository root:

```bash
python -m pytest
```

Install all optional development and documentation dependencies with:

```bash
python -m pip install -e ".[all]"
```

The sample ASD files used by the tests are stored under [`tests/sample_data`](https://github.com/KaiTastic/pyASDReader/tree/main/tests/sample_data).

## Support

Before opening an issue, check the [existing issues](https://github.com/KaiTastic/pyASDReader/issues) and include the ASD file version, instrument model, Python version, and a minimal reproduction where possible. Do not upload proprietary or sensitive spectral files.

- [Report a bug or request a feature](https://github.com/KaiTastic/pyASDReader/issues)
- [Ask a question in Discussions](https://github.com/KaiTastic/pyASDReader/discussions)
- [View the package on PyPI](https://pypi.org/project/pyASDReader/)

## License

pyASDReader is released under the [MIT License](https://github.com/KaiTastic/pyASDReader/blob/main/LICENSE).
