import requests
import os

# Test the API endpoint
def test_api():
    # Create a simple test file
    test_file_path = 'test_file.exe'
    with open(test_file_path, 'wb') as f:
        # Write some dummy executable-like data
        f.write(b'\x4D\x5A\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xFF\xFF\x00\x00')  # MZ header
        f.write(b'\xB8\x00\x00\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00\x00\x00\x00')  # More data
        f.write(b'\x00' * 1000)  # Pad to make it larger

    try:
        # Test the API
        url = 'http://localhost:5000/api/predict'
        with open(test_file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files)

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Clean up
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

if __name__ == "__main__":
    test_api()
