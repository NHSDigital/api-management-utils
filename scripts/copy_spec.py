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


def main(bucket_name: str, repo_name: str, working_directory:str):
    
    cwd = os.getcwd()
    print("Current working directory:", cwd)

    os.chdir(working_directory)
    cmdNew = os.getcwd()
    print("New working directory:", cmdNew)
    
    #spec_dir = f"{repo_name}/Specification"

    #print(f"[INFO] Checking for Specification folder at: {spec_dir}")

    #if not spec_dir.exists():
    #    print("[SKIP] No Specification folder found — skipping all processing.")
    #    return 0

    #json_file = list(Path(working_directory).glob("*.json"))

    #print(json_file)

    #if json_file:
    
    json_file = f"{repo_name}.json"
    print(f"[INFO] Found JSON file: {json_file}")
    upload_to_s3(json_file, bucket_name, repo_name)

    print("[DONE] Processing complete.")
    return 0


if __name__ == "__main__":
    print("Hitting main")

    if len(sys.argv) != 4:
        print("Usage: python copy_spec_to_s3.py <s3_bucket_name> <repo_name> <Working Directory>")
        sys.exit(1)

    bucket_name = sys.argv[1]
    repo_name = sys.argv[2]
    working_directory = sys.argv[3]
    print(f"Repo name: {repo_name}")
    print(f"Bucket name: {bucket_name}")
    print(f"Working Directory: {working_directory}")

    sys.exit(main(bucket_name,repo_name,working_directory))