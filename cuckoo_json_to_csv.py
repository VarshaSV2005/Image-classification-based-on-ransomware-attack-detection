#!/usr/bin/env python3
"""
Convert combined_cuckoo_reports.json into a clean CSV file.

Usage:
    python cuckoo_json_to_csv.py combined_cuckoo_reports.json
"""

import json
import csv
import os
import sys

OUT_CSV = "cuckoo_reports.csv"

def main(json_path):
    if not os.path.exists(json_path):
        print(f" File not found: {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    reports = data.get("reports", [])
    if not reports:
        print("No reports found inside JSON.")
        return

    rows = []
    for rep in reports:
        summary = rep.get("summary", {})

        row = {
            "source_file": summary.get("source_file", ""),
            "task_id": summary.get("task_id", ""),
            "timestamp": summary.get("timestamp", ""),

            "file_name": summary.get("file_name", ""),
            "file_md5": summary.get("file_md5", ""),
            "file_sha1": summary.get("file_sha1", ""),
            "file_sha256": summary.get("file_sha256", ""),
            "file_size": summary.get("file_size", ""),

            "signatures_count": summary.get("signatures_count", 0),
            "network_hosts_count": summary.get("network_hosts_count", 0),
            "dropped_count": summary.get("dropped_count", 0),
            "contains_malicious_word": int(bool(summary.get("contains_malicious_word", False))),
        }

        rows.append(row)

    # Write CSV
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f" CSV created successfully: {OUT_CSV}")
    print(f" Total reports written: {len(rows)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cuckoo_json_to_csv.py combined_cuckoo_reports.json")
        sys.exit(1)

    json_file = sys.argv[1]
    main(json_file)
