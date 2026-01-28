import pandas as pd
import numpy as np

# Seed for reproducibility
np.random.seed(42)

# Number of samples
n_samples = 200

# Features list
features = [
    "total_api_calls", "files_created", "registry_changes", "crypto_api_calls", "dns_queries",
    "bytes_written", "network_connections", "processes_spawned", "threads_created", "mutexes_created",
    "files_deleted", "files_modified", "registry_deleted", "sockets_opened", "urls_visited",
    "services_started", "memory_allocations", "cpu_usage", "avg_api_call_duration", "label"
]

# Helper functions
def gen_ransomware_sample():
    return {
        "total_api_calls": np.random.randint(8000, 20000),
        "files_created": np.random.randint(50, 200),
        "registry_changes": np.random.randint(40, 100),
        "crypto_api_calls": np.random.randint(10, 50),
        "dns_queries": np.random.randint(10, 50),
        "bytes_written": np.random.randint(10_000_000, 100_000_000),
        "network_connections": np.random.randint(20, 50),
        "processes_spawned": np.random.randint(3, 10),
        "threads_created": np.random.randint(40, 70),
        "mutexes_created": np.random.randint(5, 20),
        "files_deleted": np.random.randint(5, 20),
        "files_modified": np.random.randint(10, 30),
        "registry_deleted": np.random.randint(5, 15),
        "sockets_opened": np.random.randint(20, 40),
        "urls_visited": np.random.randint(5, 15),
        "services_started": np.random.randint(1, 5),
        "memory_allocations": np.random.randint(1000, 3000),
        "cpu_usage": round(np.random.uniform(30.0, 70.0), 1),
        "avg_api_call_duration": round(np.random.uniform(10.0, 20.0), 1),
        "label": 1
    }

def gen_benign_sample():
    return {
        "total_api_calls": np.random.randint(100, 1000),
        "files_created": np.random.randint(0, 10),
        "registry_changes": np.random.randint(0, 20),
        "crypto_api_calls": np.random.randint(0, 5),
        "dns_queries": np.random.randint(0, 10),
        "bytes_written": np.random.randint(100_000, 5_000_000),
        "network_connections": np.random.randint(0, 15),
        "processes_spawned": np.random.randint(0, 5),
        "threads_created": np.random.randint(1, 20),
        "mutexes_created": np.random.randint(0, 10),
        "files_deleted": np.random.randint(0, 10),
        "files_modified": np.random.randint(0, 15),
        "registry_deleted": np.random.randint(0, 5),
        "sockets_opened": np.random.randint(0, 15),
        "urls_visited": np.random.randint(0, 5),
        "services_started": np.random.randint(0, 3),
        "memory_allocations": np.random.randint(100, 1000),
        "cpu_usage": round(np.random.uniform(1.0, 20.0), 1),
        "avg_api_call_duration": round(np.random.uniform(1.0, 10.0), 1),
        "label": 0
    }

# Generate data
samples = []
for _ in range(n_samples):
    if np.random.rand() > 0.5:
        samples.append(gen_ransomware_sample())
    else:
        samples.append(gen_benign_sample())

# Create DataFrame
df = pd.DataFrame(samples, columns=features)

# Save to CSV
df.to_csv("behavioral_features_200_samples.csv", index=False)

print("CSV file 'behavioral_features_200_samples.csv' created successfully!")
