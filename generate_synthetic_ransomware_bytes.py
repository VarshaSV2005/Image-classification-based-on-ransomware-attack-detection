import random
import os

# Number of synthetic EXE samples to generate
num_samples = 200

# Approximate size of an EXE file in bytes (e.g., 1KB to 10KB for small EXEs)
min_size = 1024
max_size = 10240

# Output directory for EXE files
output_dir = 'generated_exes'
os.makedirs(output_dir, exist_ok=True)

# Common ransomware-like byte patterns/signatures
ransomware_signatures = [
    b'Your files are encrypted',
    b'Ransomware detected',
    b'Pay to decrypt',
    b'Encrypting files...',
    b'Malware signature',
    b'CryptoLocker',
    b'WannaCry',
    b'Petya',
    b'Ryuk',
    b'Conti'
]

def generate_synthetic_exe_bytes():
    # Generate a random size for the EXE
    size = random.randint(min_size, max_size)
    # Generate random bytes
    bytes_data = bytearray(random.randint(0, 255) for _ in range(size))

    # Inject ransomware-like signatures at random positions
    num_injections = random.randint(1, 5)
    for _ in range(num_injections):
        sig = random.choice(ransomware_signatures)
        if len(sig) < len(bytes_data):
            pos = random.randint(0, len(bytes_data) - len(sig))
            bytes_data[pos:pos+len(sig)] = sig

    # Add some encryption-like patterns (e.g., repeating bytes or XOR patterns)
    if random.random() > 0.5:
        # Simple XOR pattern
        key = random.randint(1, 255)
        for i in range(len(bytes_data)):
            bytes_data[i] ^= key

    return bytes_data

# Generate samples
for i in range(num_samples):
    sample = generate_synthetic_exe_bytes()
    filename = f'synthetic_ransomware_{i+1}.exe'
    filepath = os.path.join(output_dir, filename)
    with open(filepath, 'wb') as f:
        f.write(sample)

print(f"Generated {num_samples} synthetic ransomware EXE files in {output_dir}")
