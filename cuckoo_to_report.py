#!/usr/bin/env python3
r"""
cuckoo_to_report.py
Convert a folder of Cuckoo sandbox JSON result files into:
 - combined pretty JSON report (combined_cuckoo_reports.json)
 - optional CSV summary (combined_cuckoo_reports_summary.csv)

Usage:
    python cuckoo_to_report.py path_to_folder [--csv]
"""
import os
import json
import argparse
from datetime import datetime
import csv

def find_json_files(root):
    files = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(".json"):
                files.append(os.path.join(dirpath, fn))
    return sorted(files)

def safe_get(d, *keys, default=None):
    cur = d
    for k in keys:
        if cur is None:
            return default
        try:
            if isinstance(k, int):
                cur = cur[k]
            elif isinstance(cur, dict):
                cur = cur.get(k)
            else:
                return default
        except Exception:
            return default
    return cur if cur is not None else default

def extract_summary_fields(report_json):
    r = {}

    r["source_file"] = report_json.get("_report_path")

    r["task_id"] = safe_get(report_json, "info", "id")
    r["timestamp"] = safe_get(report_json, "info", "started") or safe_get(report_json, "info", "ended")

    file_block = safe_get(report_json, "target", "file", default={}) or {}
    r["file_name"] = file_block.get("name")
    r["file_md5"] = file_block.get("md5")
    r["file_sha1"] = file_block.get("sha1")
    r["file_sha256"] = file_block.get("sha256")
    r["file_size"] = file_block.get("size")

    sigs = safe_get(report_json, "signatures", default=[]) or []
    r["signatures"] = [(s.get("name") if isinstance(s, dict) else str(s)) for s in sigs]
    r["signatures_count"] = len(r["signatures"])

    hosts = set()
    for h in safe_get(report_json, "network", "hosts", default=[]) or []:
        hosts.add(h)

    for h in safe_get(report_json, "network", "http", default=[]) or []:
        if isinstance(h, dict):
            hosts.add(h.get("host") or h.get("domain") or h.get("uri") or h.get("url"))

    r["network_hosts"] = sorted(list(hosts))
    r["network_hosts_count"] = len(r["network_hosts"])

    dropped = safe_get(report_json, "dropped", default=[]) or []
    r["dropped"] = []
    for d in dropped:
        if isinstance(d, dict):
            r["dropped"].append({
                "name": d.get("name"),
                "md5": d.get("md5"),
                "sha1": d.get("sha1"),
                "sha256": d.get("sha256"),
                "size": d.get("size")
            })
        else:
            r["dropped"].append(str(d))
    r["dropped_count"] = len(r["dropped"])

    r["contains_malicious_word"] = any(
        word in json.dumps(report_json).lower()
        for word in ("malicious", "malware", "ransom", "trojan")
    )

    return r

def main():
    pa = argparse.ArgumentParser(description="Combine Cuckoo JSON reports")
    pa.add_argument("input_folder", help="Folder containing Cuckoo JSON result files")
    pa.add_argument("--csv", action="store_true", help="Also create CSV summary")
    pa.add_argument("--out", default="combined_cuckoo_reports.json", help="Output JSON file")
    args = pa.parse_args()

    json_files = find_json_files(args.input_folder)
    print(f"[INFO] Found {len(json_files)} JSON files.")

    combined = []
    errors = []

    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
        except Exception as e:
            errors.append({"file": jf, "error": str(e)})
            continue

        data["_report_path"] = jf

        try:
            summary = extract_summary_fields(data)
        except Exception as e:
            summary = {"source_file": jf, "error": str(e)}
            errors.append({"file": jf, "error_extract": str(e)})

        combined.append({"original": data, "summary": summary})

    # write JSON
    output_json = args.out
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.utcnow().isoformat(),
                "source_folder": os.path.abspath(args.input_folder),
                "reports_count": len(combined),
                "errors": errors,
                "reports": combined
            },
            f,
            indent=2,
            ensure_ascii=False
        )
    print(f"[INFO] Wrote JSON to: {output_json}")

    # write CSV
    if args.csv:
        csv_path = output_json.replace(".json", "_summary.csv")
        fields = [
            "source_file", "file_name", "file_md5", "file_sha1", "file_sha256",
            "file_size", "signatures_count", "network_hosts_count",
            "dropped_count", "contains_malicious_word"
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for rep in combined:
                s = rep["summary"]
                w.writerow({k: s.get(k, "") for k in fields})
        print(f"[INFO] Wrote CSV to: {csv_path}")

    print("[DONE] Completed with", len(errors), "errors.")
    if errors:
        print("Example error:", errors[0])

if __name__ == "__main__":
    main()
