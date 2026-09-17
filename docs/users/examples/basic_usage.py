"""
Basic usage example for pyASDReader

This script demonstrates how to read an ASD file and access its data.
"""

from pyASDReader import ASDFile
import sys

def main():
    if len(sys.argv) != 2:
        print(f"Usage: python {sys.argv[0]} path/to/file.asd")
        return

    file_path = sys.argv[1]

    print("=" * 60)
    print("pyASDReader - Basic Usage Example")
    print("=" * 60)

    # Method 1: Load file during initialization
    print("\n1. Loading ASD file...")
    asd = ASDFile(file_path)

    # Access basic information
    print(f"\n2. File Information:")
    print(f"   - File Version: {asd.asdFileVersion}")
    print(f"   - Number of channels: {len(asd.wavelengths) if asd.wavelengths is not None else 0}")

    # Access metadata
    if asd.metadata:
        print(f"\n3. Metadata:")
        print(f"   - Instrument: {asd.metadata.instrument}")
        print(f"   - File version: {asd.metadata.fileVersion}")

    # Access spectral data
    if asd.wavelengths is not None:
        print(f"\n4. Spectral Data:")
        print(f"   - Wavelength range: {asd.wavelengths[0]:.2f} - {asd.wavelengths[-1]:.2f} nm")
        print(f"   - Number of bands: {len(asd.wavelengths)}")

    # Access reflectance data
    if asd.reflectance is not None:
        print(f"\n5. Reflectance Data:")
        print(f"   - Shape: {asd.reflectance.shape}")
        print(f"   - Min: {asd.reflectance.min():.4f}")
        print(f"   - Max: {asd.reflectance.max():.4f}")
        print(f"   - Mean: {asd.reflectance.mean():.4f}")

    # Access derivatives
    if asd.reflectance1stDeriv is not None:
        print(f"\n6. Derivative Data Available:")
        print(f"   - 1st derivative: Yes")
        print(f"   - 2nd derivative: {'Yes' if asd.reflectance2ndDeriv is not None else 'No'}")

    # Access raw digital numbers
    if asd.digitalNumber is not None:
        print(f"\n7. Raw Data (DN):")
        print(f"   - Shape: {asd.digitalNumber.shape}")

    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
