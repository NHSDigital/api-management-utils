import os
import sys
import boto3
import json
from pathlib import Path
from botocore.exceptions import ClientError

def upload_to_s3(file_path: Path, bucket_name: str, folder_name: str):
    """Upload one file to the given S3 bucket under folder_name/."""
    s3 = boto3.client("s3")
    key = f"apis/{folder_name}/{file_path}"

    try:
        s3.upload_file(str(file_path), bucket_name, key)
        print(f"[OK] Uploaded → s3://{bucket_name}/apis/{key}")
    except ClientError as e:
        print(f"[ERROR] Upload failed: {file_path} → s3://{bucket_name}/{key}")
        print(e)
        sys.exit(1)


def main(bucket_name: str, repo_name: str):
    cwd = os.getcwd()
    print("Current working directory:", cwd)

    root_dir = Path.cwd().parents[1]
    json_file = root_dir / f"{repo_name}.json"
    dst_json_file = root_dir / "spec.json"
    
    print(json_file)

    if not json_file.is_file():
        print(f"[ERROR] JSON spec not found: {json_file}")
        return 1

    dst_json_file.write_bytes(json_file.read_bytes())
    
    print(dst_json_file)

    upload_to_s3("spec.json", bucket_name, repo_name)

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