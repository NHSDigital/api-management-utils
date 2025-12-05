#!/usr/bin/env python3
import os
import sys
import json
import yaml
import boto3
from pathlib import Path
from botocore.exceptions import ClientError

def convert_yaml_to_json(yaml_path: Path, output_dir: Path) -> Path:
    """Convert YAML file to JSON and return output file path."""
    try:
        with open(yaml_path, "r") as yf:
            data = yaml.safe_load(yf)
    except Exception as e:
        print(f"Error reading YAML file {yaml_path}: {e}")
        raise

    json_filename = yaml_path.stem + ".json"
    output_path = output_dir / json_filename

    try:
        with open(output_path, "w") as jf:
            json.dump(data, jf, indent=2)
    except Exception as e:
        print(f"Error writing JSON file {output_path}: {e}")
        raise

    print(f"[OK] Converted {yaml_path} → {output_path}")
    return output_path


def upload_to_s3(file_path: Path, bucket_name: str, folder_name: str):
    """Upload one file to the given S3 bucket under folder_name/."""
    s3 = boto3.client("s3")
    key = f"{folder_name}/{file_path.name}"

    try:
        s3.upload_file(str(file_path), bucket_name, key)
        print(f"[OK] Uploaded → s3://{bucket_name}/{key}")
    except ClientError as e:
        print(f"[ERROR] Upload failed: {file_path} → s3://{bucket_name}/{key}")
        print(e)
        sys.exit(1)


def main(bucket_name: str, repo_name: str):
    
    spec_dir = repo_name / "Specification"

    print(f"[INFO] Checking for Specification folder at: {spec_dir}")

    if not spec_dir.exists():
        print("[SKIP] No Specification folder found — skipping all processing.")
        return 0

    yaml_files = list(spec_dir.glob("*.yaml")) + list(spec_dir.glob("*.yml"))

    if not yaml_files:
        print("[SKIP] Specification folder exists, but no YAML files found — skipping.")
        return 0

    output_dir = Path("spec_output")
    output_dir.mkdir(exist_ok=True)

    generated_files = []

    print(f"[INFO] Found {len(yaml_files)} YAML file(s). Converting...")

    for yaml_file in yaml_files:
        json_file = convert_yaml_to_json(yaml_file, output_dir)
        generated_files.append(json_file)

    print(f"[INFO] Uploading {len(generated_files)} file(s) to S3 bucket '{bucket_name}'...")
    for json_file in generated_files:
        upload_to_s3(json_file, bucket_name, repo_name)

    print("[DONE] Processing complete.")
    return 0


if __name__ == "__main__":
    print("Hitting main")
    if len(sys.argv) != 3:
        print("Usage: python copy_spec_to_s3.py <s3_bucket_name> <repo_name>")
        sys.exit(1)

    bucket_name = sys.argv[1]
    repo_name = sys.argv[2]
    print(f"Repo name: {repo_name}")
    print(f"Bucket name: {bucket_name}")

    sys.exit(main(bucket_name,repo_name))