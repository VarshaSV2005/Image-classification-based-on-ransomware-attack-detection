#!/usr/bin/env python3
"""
Test script for file monitoring functionality
"""
import os
import time
import tempfile

def test_file_monitoring():
    """Test the file monitoring by creating a test executable file"""

    # Create a temporary executable file for testing
    with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as temp_file:
        # Write some dummy executable content (this is just for testing)
        dummy_content = b'\x4D\x5A\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xFF\xFF\x00\x00'  # MZ header
        dummy_content += b'\xB8\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00' * 100  # More dummy bytes
        temp_file.write(dummy_content)
        temp_file_path = temp_file.name

    print(f"Created test file: {temp_file_path}")

    # Move the file to Desktop directory to trigger monitoring
    desktop_dir = os.path.expanduser("~/Desktop")
    if not os.path.exists(desktop_dir):
        os.makedirs(desktop_dir)

    test_file_path = os.path.join(desktop_dir, "test_ransomware.exe")

    # Copy the file to Desktop
    with open(temp_file_path, 'rb') as src, open(test_file_path, 'wb') as dst:
        dst.write(src.read())

    print(f"Test file placed in Desktop: {test_file_path}")
    print("Monitoring should detect this file and analyze it...")
    print("Check the Flask app logs and quarantine directory for results.")

    # Clean up temp file
    os.unlink(temp_file_path)

    # Wait a bit for monitoring to detect
    time.sleep(5)

    # Check if file was quarantined
    quarantine_dir = os.path.join(os.getcwd(), 'quarantine')
    if os.path.exists(quarantine_dir):
        quarantined_files = os.listdir(quarantine_dir)
        if quarantined_files:
            print(f"✅ File was quarantined: {quarantined_files}")
        else:
            print("❌ No files in quarantine directory")
    else:
        print("❌ Quarantine directory does not exist")

if __name__ == "__main__":
    print("Testing file monitoring functionality...")
    test_file_monitoring()
    print("Test completed.")
