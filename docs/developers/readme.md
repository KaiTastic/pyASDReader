# Core Class Design

The class diagram below shows the main relationships in `pyASDReader`.

## Core classes

`ASDFile` is the main public class for reading ASD binary files. It inherits
from `FileAttributes`, which provides general file information such as the
file path, size, timestamps, permissions, and content hashes. The ASD-specific
parser is responsible for decoding the binary stream and exposing the decoded
sections as attributes on the `ASDFile` instance.

The format-specific values used during parsing are defined in `constant.py`.
These enums represent file versions, instrument types, spectrum and data
formats, calibration series, integration times, and signature or audit states.

## Parsing flow

When a file path is passed to `ASDFile`, the file is loaded automatically. The
`read()` method then parses the stream in the order defined by the ASD file
format:

1. File version and metadata header.
2. Wavelengths and primary spectrum data.
3. Reference file header and reference data for version 2 and later.
4. Classifier data and dependent variables for version 6 and later.
5. Calibration header and calibration series for version 7 and later.
6. Audit log and digital signature for version 8 and later.

Each section is parsed using the current byte offset. The parser advances the
offset after successfully decoding a section, so later sections can be read
without reinterpreting earlier bytes. The `wavelengths` array is derived from
the metadata channel count, first wavelength, and wavelength step.

## Version compatibility

The version checks in `read()` are intentional: older ASD files do not contain
the sections introduced by later format versions. Consumers should therefore
check whether an optional attribute is `None` before using it, especially for
classifier, calibration, audit-log, and signature data.

## Visual Paradigm source files

<a href="https://www.visual-paradigm.com/"><img src="https://cdn-images.visual-paradigm.com/media/vplogo_72.png" alt="Visual Paradigm logo" width="120"></a>

The editable class-design source is maintained as a Visual Paradigm project:

- [`Core_Class_Design.vpp`](architecture/class_design/Core_Class_Design.vpp) is the primary project file. Open it with Visual Paradigm to inspect or update the class diagram and its model elements.

![pyASDReader core class design](architecture/class_diagram/Core_Class_Design.jpg)

[Download the PDF version](architecture/class_diagram/Core_Class_Design.pdf).
