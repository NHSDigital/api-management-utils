#!/usr/bin/env python3
import os
import sys
import boto3
from pathlib import Path
from botocore.exceptions import ClientError

def upload_to_s3(file_path: Path, bucket_name: str, folder_name: str):
    """Upload one file to the given S3 bucket under folder_name/."""
    s3 = boto3.client("s3")
    key = f"{folder_name}/{file_path}"

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

    # Go up one level to reach utils/
    utils_dir = os.path.dirname(os.getcwd())
    print("Utils directory:", utils_dir)

    json_file = f"{repo_name}.json"

    # Build path to JSON file
    json_path = os.path.join(utils_dir, json_file)

    upload_to_s3(json_path, bucket_name, repo_name)

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