### pyASDReader - A Python Library for ASD Spectral File Reading

[![PyPI version](https://img.shields.io/pypi/v/pyASDReader?style=flat-square)](https://pypi.org/project/pyASDReader/)
[![Python versions](https://img.shields.io/pypi/pyversions/pyASDReader?style=flat-square)](https://pypi.org/project/pyASDReader/)
[![License](https://img.shields.io/github/license/KaiTastic/pyASDReader?style=flat-square)](https://github.com/KaiTastic/pyASDReader/blob/main/LICENSE)
[![Tests](https://img.shields.io/github/actions/workflow/status/KaiTastic/pyASDReader/python-package.yml?branch=main&label=tests&style=flat-square)](https://github.com/KaiTastic/pyASDReader/actions)
[![Coverage](https://img.shields.io/codecov/c/github/KaiTastic/pyASDReader?style=flat-square)](https://codecov.io/gh/KaiTastic/pyASDReader)
[![Downloads](https://pepy.tech/badge/pyasdreader)](https://pepy.tech/project/pyasdreader)

pyASDReader is a robust Python library designed to read and parse all versions (v1-v8) of ASD (Analytical Spectral Devices) binary spectral files. It provides seamless access to spectral data, metadata, and calibration information from various ASD instruments including FieldSpec, LabSpec, TerraSpec, and more.

---

## 🚀 Key Features

- **Universal Compatibility**: Supports all ASD file versions (v1-v8) and instruments
  - FieldSpec series (4 Hi-Res NG, 4 Hi-Res, 4 Standard-Res, 4 Wide-Res)
  - LabSpec series (4 Bench, 4 Hi-Res, 4 Standard-Res)
  - TerraSpec series (4 Hi-Res, 4 Standard-Res)
  - HandHeld series (2 Pro, 2), AgriSpec, and more
  
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

- Python >=3.8
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

- **[CHANGELOG](CHANGELOG.md)** - Version history, feature updates, and bug fixes
- **[Version Management Guide](VERSION_MANAGEMENT.md)** - Release workflow, branch strategy, and CI/CD automation
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

## Usage Examples

### Basic Spectral Data Access

```python
import numpy as np
import matplotlib.pyplot as plt
from pyASDReader import ASDFile

# Load ASD file
asd = ASDFile("sample_spectrum.asd")

# Basic information
print(f"File version: {asd.asdFileVersion}")
print(f"Instrument: {asd.metadata.instrumentModel}")
print(f"Number of channels: {len(asd.wavelengths)}")
print(f"Spectral range: {asd.wavelengths[0]:.1f} - {asd.wavelengths[-1]:.1f} nm")

# Plot spectrum
plt.figure(figsize=(10, 6))
plt.plot(asd.wavelengths, asd.reflectance)
plt.xlabel('Wavelength (nm)')
plt.ylabel('Reflectance')
plt.title('ASD Spectrum')
plt.grid(True)
plt.show()
```

### Advanced Spectral Analysis

```python
# Access different spectral measurements
reflectance = asd.reflectance                 # Raw reflectance
abs_reflectance = asd.absoluteReflectance     # Absolute reflectance
radiance = asd.radiance                       # Radiance data
irradiance = asd.irradiance                   # Irradiance data

# Derivative calculations
refl_1st_deriv = asd.reflectance1stDeriv      # First derivative
refl_2nd_deriv = asd.reflectance2ndDeriv      # Second derivative

# Log(1/R) transformations
log1r = asd.log1R                             # Log(1/R)
log1r_1st_deriv = asd.log1R1stDeriv          # Log(1/R) first derivative
log1r_2nd_deriv = asd.log1R2ndDeriv          # Log(1/R) second derivative
```

### Error Handling and Validation

```python
from pyASDReader import ASDFile
import os

def safe_read_asd(file_path):
    """Safely read ASD file with error handling."""
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"ASD file not found: {file_path}")
        
        # Load the file
        asd = ASDFile(file_path)
        
        # Validate data
        if asd.wavelengths is None or len(asd.wavelengths) == 0:
            raise ValueError("Invalid or empty wavelength data")
        
        if asd.reflectance is None or len(asd.reflectance) == 0:
            raise ValueError("Invalid or empty reflectance data")
        
        print(f"✓ Successfully loaded: {os.path.basename(file_path)}")
        print(f"  Channels: {len(asd.wavelengths)}")
        print(f"  Range: {asd.wavelengths[0]:.1f}-{asd.wavelengths[-1]:.1f} nm")
        
        return asd
        
    except Exception as e:
        print(f"✗ Error loading {file_path}: {str(e)}")
        return None

# Usage
asd_file = safe_read_asd("spectrum.asd")
if asd_file is not None:
    # Process the file
    pass
```

### Batch Processing

```python
import glob
from pathlib import Path

def process_asd_directory(directory_path, output_format='csv'):
    """Process all ASD files in a directory."""
    asd_files = glob.glob(os.path.join(directory_path, "*.asd"))
    
    print(f"Found {len(asd_files)} ASD files")
    
    for file_path in asd_files:
        try:
            asd = ASDFile(file_path)
            
            # Extract filename without extension
            base_name = Path(file_path).stem
            
            if output_format == 'csv':
                # Save as CSV
                output_path = f"{base_name}_spectrum.csv"
                data = np.column_stack([asd.wavelengths, asd.reflectance])
                np.savetxt(output_path, data, delimiter=',', 
                          header='Wavelength(nm),Reflectance', comments='')
                print(f"✓ Saved: {output_path}")
                
        except Exception as e:
            print(f"✗ Error processing {file_path}: {str(e)}")

# Usage
process_asd_directory("./asd_data/", output_format='csv')
```

## API Reference

### Core Classes

#### `ASDFile`

The main class for reading and parsing ASD files.

**Constructor:**
```python
ASDFile(file_path: str = None)
```

**Key Properties:**
| Property | Type | Description |
|----------|------|-------------|
| `wavelengths` | `numpy.ndarray` | Wavelength array (nm) |
| `reflectance` | `numpy.ndarray` | Reflectance values |
| `absoluteReflectance` | `numpy.ndarray` | Absolute reflectance |
| `radiance` | `numpy.ndarray` | Radiance data |
| `irradiance` | `numpy.ndarray` | Irradiance data |
| `reflectance1stDeriv` | `numpy.ndarray` | First derivative of reflectance |
| `reflectance2ndDeriv` | `numpy.ndarray` | Second derivative of reflectance |
| `log1R` | `numpy.ndarray` | Log(1/R) transformation |
| `log1R1stDeriv` | `numpy.ndarray` | First derivative of Log(1/R) |
| `log1R2ndDeriv` | `numpy.ndarray` | Second derivative of Log(1/R) |
| `metadata` | `object` | File metadata and instrument info |
| `asdFileVersion` | `int` | ASD file format version |

**Methods:**
```python
read(file_path: str) -> None
    """Load and parse an ASD file."""
```

## Technical Documentation

### ASD File Format Support

pyASDReader supports all ASD file format versions and instrument models:

#### Supported Instruments

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

