import os
import random
import struct
from pathlib import Path

def generate_exe_header():
    # DOS Header
    dos_header = struct.pack('<H', 0x5A4D)  # MZ signature
    dos_header += struct.pack('<H', 0x0090)  # Bytes on last page
    dos_header += struct.pack('<H', 0x0003)  # Pages in file
    dos_header += struct.pack('<H', 0x0000)  # Relocations
    dos_header += struct.pack('<H', 0x0004)  # Size of header in paragraphs
    dos_header += struct.pack('<H', 0x0010)  # Minimum extra paragraphs
    dos_header += struct.pack('<H', 0xFFFF)  # Maximum extra paragraphs
    dos_header += struct.pack('<H', 0x0000)  # Initial SS
    dos_header += struct.pack('<H', 0x00B8)  # Initial SP
    dos_header += struct.pack('<H', 0x0000)  # Checksum
    dos_header += struct.pack('<H', 0x0000)  # Initial IP
    dos_header += struct.pack('<H', 0x0000)  # Initial CS
    dos_header += struct.pack('<H', 0x0040)  # File address of relocation table
    dos_header += struct.pack('<H', 0x0000)  # Overlay number
    dos_header += struct.pack('<8H', 0, 0, 0, 0, 0, 0, 0, 0)  # Reserved words
    dos_header += struct.pack('<H', 0x0000)  # OEM identifier
    dos_header += struct.pack('<H', 0x0000)  # OEM information
    dos_header += struct.pack('<20H', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)  # Reserved words
    dos_header += struct.pack('<L', 0x00000080)  # File address of new exe header

    # PE Header
    pe_header = struct.pack('<L', 0x00004550)  # PE signature
    pe_header += struct.pack('<H', 0x014C)  # Machine (IMAGE_FILE_MACHINE_I386)
    pe_header += struct.pack('<H', 0x0001)  # Number of sections
    pe_header += struct.pack('<L', 0x5B7F0E00)  # Time date stamp
    pe_header += struct.pack('<L', 0x00000000)  # Pointer to symbol table
    pe_header += struct.pack('<L', 0x00000000)  # Number of symbols
    pe_header += struct.pack('<H', 0x00E0)  # Size of optional header
    pe_header += struct.pack('<H', 0x0102)  # Characteristics

    # Optional Header
    optional_header = struct.pack('<H', 0x010B)  # Magic (PE32)
    optional_header += struct.pack('<B', 0x0E)  # Major linker version
    optional_header += struct.pack('<B', 0x00)  # Minor linker version
    optional_header += struct.pack('<L', 0x00001000)  # Size of code
    optional_header += struct.pack('<L', 0x00001000)  # Size of initialized data
    optional_header += struct.pack('<L', 0x00000000)  # Size of uninitialized data
    optional_header += struct.pack('<L', 0x00001000)  # Address of entry point
    optional_header += struct.pack('<L', 0x00001000)  # Base of code
    optional_header += struct.pack('<L', 0x00002000)  # Base of data
    optional_header += struct.pack('<L', 0x00400000)  # Image base
    optional_header += struct.pack('<L', 0x00001000)  # Section alignment
    optional_header += struct.pack('<L', 0x00000200)  # File alignment
    optional_header += struct.pack('<H', 0x0004)  # Major OS version
    optional_header += struct.pack('<H', 0x0000)  # Minor OS version
    optional_header += struct.pack('<H', 0x0000)  # Major image version
    optional_header += struct.pack('<H', 0x0000)  # Minor image version
    optional_header += struct.pack('<H', 0x0004)  # Major subsystem version
    optional_header += struct.pack('<H', 0x0000)  # Minor subsystem version
    optional_header += struct.pack('<L', 0x00000000)  # Win32 version value
    optional_header += struct.pack('<L', 0x00003000)  # Size of image
    optional_header += struct.pack('<L', 0x00000200)  # Size of headers
    optional_header += struct.pack('<L', 0x00000000)  # Checksum
    optional_header += struct.pack('<H', 0x0002)  # Subsystem (Windows GUI)
    optional_header += struct.pack('<H', 0x0000)  # DLL characteristics
    optional_header += struct.pack('<L', 0x00100000)  # Size of stack reserve
    optional_header += struct.pack('<L', 0x00001000)  # Size of stack commit
    optional_header += struct.pack('<L', 0x00100000)  # Size of heap reserve
    optional_header += struct.pack('<L', 0x00001000)  # Size of heap commit
    optional_header += struct.pack('<L', 0x00000000)  # Loader flags
    optional_header += struct.pack('<L', 0x00000010)  # Number of RVA and sizes

    # Data directories (16 entries, each 8 bytes)
    for _ in range(16):
        optional_header += struct.pack('<L', 0x00000000)  # RVA
        optional_header += struct.pack('<L', 0x00000000)  # Size

    # Section Header
    section_header = struct.pack('<8s', b'.text\x00\x00\x00')  # Name
    section_header += struct.pack('<L', 0x00001000)  # Virtual size
    section_header += struct.pack('<L', 0x00001000)  # Virtual address
    section_header += struct.pack('<L', 0x00001000)  # Size of raw data
    section_header += struct.pack('<L', 0x00000200)  # Pointer to raw data
    section_header += struct.pack('<L', 0x00000000)  # Pointer to relocations
    section_header += struct.pack('<L', 0x00000000)  # Pointer to line numbers
    section_header += struct.pack('<H', 0x0000)  # Number of relocations
    section_header += struct.pack('<H', 0x0000)  # Number of line numbers
    section_header += struct.pack('<L', 0x60000020)  # Characteristics

    return dos_header + pe_header + optional_header + section_header

def generate_exe_file(filename, size=4096):
    header = generate_exe_header()

    # Ransomware-like patterns and strings
    ransomware_patterns = [ b"safe",b"sample", ]

def main():
    output_dir = Path('sv_file_exe')
    output_dir.mkdir(exist_ok=True)

    num_files = 10
    for i in range(num_files):
        filename = output_dir / f'ransomware_exe_{i+1}.exe'
        generate_exe_file(filename)
        print(f"Generated {filename}")

    print(f"Generated {num_files} EXE files in {output_dir}")

if __name__ == "__main__":
    main()
    