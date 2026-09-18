### pyASDReader - A Python Library for ASD Spectral File Reading

[![PyPI version](https://img.shields.io/pypi/v/pyASDReader?style=flat-square)](https://pypi.org/project/pyASDReader/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyASDReader?style=flat-square)](https://pypi.org/project/pyASDReader/)
[![License](https://img.shields.io/github/license/KaiTastic/pyASDReader?style=flat-square)](https://github.com/KaiTastic/pyASDReader/blob/main/LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/KaiTastic/pyASDReader/python-package.yml?branch=main&label=tests&style=flat-square)](https://github.com/KaiTastic/pyASDReader/actions)
[![Coverage](https://img.shields.io/codecov/c/github/KaiTastic/pyASDReader?style=flat-square)](https://codecov.io/gh/KaiTastic/pyASDReader)
[![Downloads](https://pepy.tech/badge/pyasdreader)](https://pepy.tech/project/pyasdreader)
[![Documentation](https://img.shields.io/badge/docs-Read%20the%20Docs-ea580c?style=flat-square)](https://pyasdreader.readthedocs.io/)

pyASDReader is a robust Python library designed to read and parse all versions (v1-v8) of ASD (Analytical Spectral Devices) binary spectral files. It provides seamless access to spectral data, metadata, and calibration information from various ASD instruments including FieldSpec, LabSpec, TerraSpec, and more.

---

## 🚀 Key Features

pyASDReader supports all ASD file format versions and instrument models:

- **Universal Compatibility**: Supports all ASD file versions (v1-v8) and instruments

    | **FieldSpec Series** | **LabSpec Series** | **TerraSpec Series** |
    |---------------------|-------------------|---------------------|
    | FieldSpec 4 Hi-Res NG | LabSpec 4 Bench | TerraSpec 4 Hi-Res |
    | FieldSpec 4 Hi-Res | LabSpec 4 Hi-Res | TerraSpec 4 Standard-Res |
    | FieldSpec 4 Standard-Res | LabSpec 4 Standard-Res | |
    | FieldSpec 4 Wide-Res | LabSpec range | |

    | **HandHeld Series** | **Other Models** |
    |-------------------|------------------|
    | HandHeld 2 Pro | AgriSpec |
    | HandHeld 2 | |

- **Comprehensive Data Access**: Extract all spectral information
  - Spectral data (reflectance, radiance, irradiance)
  - Wavelength arrays and derivative calculations
  - Complete metadata and instrument parameters
  - Calibration data and reference measurements
  
- **Advanced Processing**: Built-in spectral analysis tools
  - First and second derivative calculations
  - Log(1/R) transformations
  - Type-safe enum constants for file attributes
  - Robust error handling and validation

## Requirements

- Python >=3.9
- numpy >=1.20.0

## Installation

### Stable Release (Recommended)

```bash
pip install pyASDReader
```

### Development Installation

For contributors and advanced users:

```bash
# Clone the repository
git clone https://github.com/KaiTastic/pyASDReader.git
cd pyASDReader

# Install in editable mode with development dependencies
pip install -e ".[dev]"

# Install with all dependencies (dev + docs + testing)
pip install -e ".[all]"
```

## Documentation

### Full online documentation

- **[Read the Docs](https://pyasdreader.readthedocs.io/)** - Full online documentation

### Project documentation

- **[CHANGELOG](CHANGELOG.md)** - Version history, feature updates, and bug fixes
- **[Version Management Guide](docs/maintainers/VERSION_MANAGEMENT.md)** - Release workflow, branch strategy, and CI/CD automation
- **[GitHub Issues](https://github.com/KaiTastic/pyASDReader/issues)** - Report bugs and request features
- **[GitHub Discussions](https://github.com/KaiTastic/pyASDReader/discussions)** - Ask questions and share ideas

## Quick Start

```python
from pyASDReader import ASDFile

# Method 1: Load file during initialization
asd_file = ASDFile("path/to/your/spectrum.asd")

# Method 2: Create instance first, then load
asd_file = ASDFile()
asd_file.read("path/to/your/spectrum.asd")

# Access basic data
wavelengths = asd_file.wavelengths    # Wavelength array
reflectance = asd_file.reflectance    # Reflectance values
metadata = asd_file.metadata          # File metadata
```

## Technical Documentation

#### File Structure Mapping

| **ASD File Component** | **pyASDReader Property** |
|----------------------|-------------------------|
| Spectrum File Header | `asdFileVersion`, `metadata` |
| Spectrum Data | `spectrumData` |
| Reference File Header | `referenceFileHeader` |
| Reference Data | `referenceData` |
| Classifier Data | `classifierData` |
| Dependent Variables | `dependants` |
| Calibration Header | `calibrationHeader` |
| Absolute/Base Calibration | `calibrationSeriesABS`, `calibrationSeriesBSE` |
| Lamp Calibration Data | `calibrationSeriesLMP` |
| Fiber Optic Data | `calibrationSeriesFO` |
| Audit Log | `auditLog` |
| Digital Signature | `signature` |

### Validation and Testing

pyASDReader has been extensively tested against **ASD ViewSpecPro 6.2.0** to ensure accuracy:

#### ✅ **Validated Features**
- Digital Number (DN) values
- Reflectance calculations (raw, 1st derivative, 2nd derivative)
- Absolute reflectance computations
- Log(1/R) transformations (raw, 1st derivative, 2nd derivative)
- Wavelength accuracy and calibration

#### 🔄 **In Development**
- Radiance calculations
- Irradiance processing  
- Parabolic jump correction algorithms

### Upcoming Features

#### Spectral Discontinuities Correction

Advanced correction algorithms for spectral jumps at detector boundaries:

- **Hueni Method**: Temperature-based correction using empirical formulas
- **ASD Parabolic Method**: Parabolic interpolation for jump correction
- Support for both automated and manual correction parameters

#### Enhanced File Format Conversion

Comprehensive export capabilities beyond the standard ASCII format:
- Multiple output formats (CSV, JSON, HDF5, NetCDF)
- Customizable data selection and filtering
- Batch processing with parallel execution
- Integration with popular spectral analysis libraries

#### Resampling

Advanced spectral resampling capabilities for data standardization and cross-instrument comparison:

**Key Features:**
- **Multi-method interpolation**: Linear, cubic spline, and higher-order interpolation
- **Instrument-aware resampling**: Optional consideration of Spectral Response Functions (SRF)
- **Flexible wavelength grids**: Custom intervals (e.g., 1 nm, 5 nm, 10 nm) or target wavelength arrays
- **Physical accuracy**: SRF convolution for accurate cross-instrument data alignment

**Use Cases:**
- Standardize spectral resolution across multiple measurements
- Align ASD data with satellite sensor bands (e.g., Sentinel-2, Landsat, EnMap, GF-5)
- Match reference spectral libraries with different sampling intervals
- Prepare datasets for machine learning models requiring uniform wavelength grids

#### Graphic User Interface

User-friendly desktop application for interactive ASD file analysis and visualization:

**Key Features:**
- **Intuitive File Management**:
  - Drag-and-drop file loading
  - Batch processing of multiple ASD files
  - Directory browser with file preview
  - Recent file history

- **Interactive Visualization**:
  - Real-time spectral plotting with zoom/pan controls
  - Multiple spectra overlay and comparison
  - Customizable plot styles (line color, width, markers)
  - Export plots to high-resolution images (PNG, SVG, PDF)

- **Data Processing Tools**:
  - One-click derivative calculations (1st, 2nd order)
  - Log(1/R) transformations
  - Spectral resampling with visual preview
  - Jump correction at detector boundaries

- **Metadata Viewer**:
  - Comprehensive instrument information display
  - Acquisition parameters and settings
  - Calibration status and timestamps
  - GPS coordinates and measurement notes

- **Export Options**:
  - Multiple format support (CSV, Excel, JSON, HDF5)
  - Customizable column selection
  - Batch export with naming templates
  - Direct integration with spectral analysis software

## Citation

If you use pyASDReader in your research, please cite it using the following information:

**BibTeX format**:
```bibtex
@software{pyASDReader,
  author = {Cao, Kai},
  title = {pyASDReader: A Python Library for ASD Spectral File Reading},
  year = {2025},
  url = {https://github.com/KaiTastic/pyASDReader},
  version = {1.2.3}
}
```

**Plain text citation**:
```
Cao, Kai. (2025). pyASDReader: A Python Library for ASD Spectral File Reading. Available at: https://github.com/KaiTastic/pyASDReader
```

## References

### Official Documentation
- [ASD Inc. (2017). ASD File Format: Version 8 (Revision): 1-10](https://www.malvernpanalytical.com/en/learn/knowledge-center/user-manuals/asd-file-format-v8)
- ASD Inc. Indico Version 7 File Format: 1-9
- ASD Inc. (2008). ViewSpec Pro User Manual: 1-24  
- ASD Inc. (2015). FieldSpec 4 User Manual: 1-10

### Scientific References
- [Hueni, A. and A. Bialek (2017). "Cause, Effect, and Correction of Field Spectroradiometer Interchannel Radiometric Steps." IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing 10(4): 1542-1551](https://ieeexplore.ieee.org/document/7819458)

## License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for complete details.

---

<div align="center">

**[⬆ Back to Top](#pyasdreader)**

Made with ❤️ for the spectroscopy community

[![GitHub stars](https://img.shields.io/github/stars/KaiTastic/pyASDReader?style=social)](https://github.com/KaiTastic/pyASDReader/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/KaiTastic/pyASDReader?style=social)](https://github.com/KaiTastic/pyASDReader/network/members)

</div>

