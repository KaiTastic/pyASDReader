# User Guide

```{toctree}
:maxdepth: 1
:hidden:

examples/README
```

`pyASDReader` reads ASD binary spectral files and exposes their wavelengths,
measurements, metadata, and version-dependent sections through a Python API.
This guide focuses on the common workflow after installation. For the full
API table and project overview, see the [main README](https://github.com/KaiTastic/pyASDReader#readme).

## Install

Install the latest release from PyPI:

```bash
python -m pip install pyASDReader
```

The package requires Python 3.8 or newer and NumPy 1.20 or newer.

## Read a file

Pass the path to an `.asd` file when creating `ASDFile`:

```python
from pyASDReader import ASDFile

asd = ASDFile("path/to/spectrum.asd")

print(f"ASD version: {asd.asdFileVersion}")
print(f"Channels: {len(asd.wavelengths)}")
print(f"Wavelengths: {asd.wavelengths[0]}-{asd.wavelengths[-1]} nm")
```

To reuse an object, construct it without a path and call `read()` later:

```python
asd = ASDFile()
if not asd.read("path/to/spectrum.asd"):
		raise RuntimeError("The ASD file could not be read")
```

`read()` returns `True` after the parser accepts the file and `False` for an
invalid path, missing file, unsupported version, or parsing failure. This
library is currently a read-only parser; use a separate export workflow when
you need to write processed data to CSV or another format.

## Work with measurements

The wavelength array and measurement arrays have matching channel order and
can be passed directly to NumPy or plotting libraries:

```python
import matplotlib.pyplot as plt

plt.plot(asd.wavelengths, asd.reflectance)
plt.xlabel("Wavelength (nm)")
plt.ylabel("Reflectance")
plt.show()
```

Common measurements and derived values include:

| Attribute | Description |
| --- | --- |
| `wavelengths` | Wavelength values in nanometers |
| `reflectance` | Reflectance spectrum |
| `absoluteReflectance` | Absolute reflectance spectrum |
| `radiance` | Radiance data |
| `irradiance` | Irradiance data |
| `reflectance1stDeriv` | First reflectance derivative |
| `reflectance2ndDeriv` | Second reflectance derivative |
| `log1R` | `log(1/R)` transformation |

Check an attribute before using it when the source file may not contain that
measurement:

```python
if asd.reflectance is not None:
		mean_reflectance = asd.reflectance.mean()
```

## Inspect metadata

The `metadata` object contains file and instrument information. The exact
fields depend on the instrument and ASD format version:

```python
if asd.metadata is not None:
		print(asd.metadata.instrumentModel)
		print(asd.metadata.instrumentType)
		print(asd.metadata.fileVersion)
```

Reference, classifier, dependent-variable, calibration, audit-log, and digital
signature data are also version-dependent. Treat these sections as optional
when processing files from multiple instrument generations.

## Process a directory

For a batch workflow, enumerate files with `pathlib` and handle each file
independently so one invalid file does not hide which input failed:

```python
from pathlib import Path
from pyASDReader import ASDFile

for file_path in Path("asd_data").glob("*.asd"):
		try:
				asd = ASDFile(str(file_path))
				if asd.wavelengths is None or asd.reflectance is None:
						print(f"Skipping incomplete file: {file_path}")
						continue
				print(file_path.name, len(asd.wavelengths))
		except (OSError, ValueError) as error:
				print(f"Could not read {file_path}: {error}")
```

## Examples and sample data

The repository includes a runnable example in
[`docs/users/examples/basic_usage.py`](https://github.com/KaiTastic/pyASDReader/blob/main/docs/users/examples/basic_usage.py).
The test fixtures under
[`tests/sample_data`](https://github.com/KaiTastic/pyASDReader/tree/main/tests/sample_data)
cover several ASD format versions and are useful for local experiments.
Replace fixture paths with your own files in production code.

## Troubleshooting

- **The file cannot be read:** confirm that the path points to a binary `.asd`
	file and that the process has permission to open it.
- **An attribute is `None`:** the field may be absent from the instrument or
	from the ASD version being processed; check for `None` before use.
- **The wavelength and measurement lengths differ:** treat this as invalid
	input and report the file rather than pairing values by truncating arrays.
- **The instrument or version is unexpected:** inspect `metadata` and
	`asdFileVersion`, then include both values when opening an issue.

When reporting a problem, include a minimal reproduction, Python version, ASD
format version, and instrument model. Do not upload proprietary or sensitive
spectral files.
