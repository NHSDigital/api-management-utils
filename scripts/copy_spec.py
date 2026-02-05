import os
import sys
from typing import Optional
import boto3
import hashlib
import json
from pathlib import Path
from botocore.exceptions import ClientError

def _metadata(spec_hash: Optional[str], temporary: Optional[bool] = False):
    metadata = {}
    proxygen_version = '453743-sha907aa22b'
    if spec_hash is not None:
        metadata["spec_hash"] = spec_hash

    if temporary is not None:
        metadata["temporary"] = str(temporary)

    if proxygen_version is not None:
        metadata["proxygen_version"] = proxygen_version

    return metadata or None

def upload_to_s3(file_path: Path, bucket_name: str, folder_name: str, spec_hash: str, temporary: bool = False):
    """
    Upload a file to S3 with:
    - ACL bucket-owner-full-control
    - metadata including MD5 hash + temporary flag + proxygen_version
    """
    s3 = boto3.client("s3")

    # S3 key
    key = f"apis/{folder_name}/{file_path}"

    # --- Compute MD5 Hash for Metadata ---
    #spec_json = file_path.read_text(encoding="utf-8")
    #spec_hash = hashlib.md5(spec_json.encode("utf-8")).hexdigest()

    # Build complete metadata
    metadata = _metadata(spec_hash=spec_hash, temporary=temporary)

    # Build ExtraArgs
    extra_args = {
        "ACL": "bucket-owner-full-control"
    }

    if metadata:
        # Metadata must be lowercase keys, values must be strings
        extra_args["Metadata"] = metadata

    try:
        s3.upload_file(
            Filename=str(file_path),
            Bucket=bucket_name,
            Key=key,
            ExtraArgs=extra_args
        )
        print(f"[OK] Uploaded → s3://{bucket_name}/{key}")
        print(f"[META] {metadata}")

    except ClientError as e:
        print(f"[ERROR] Upload failed: {file_path} → s3://{bucket_name}/{key}")
        print(e)
        sys.exit(1)

def main(bucket_name: str, repo_name: str):
    cwd = os.getcwd()
    print("Current working directory:", cwd)

    root_dir = Path.cwd().parents[1]
    json_file = root_dir / f"{repo_name}.json"
    dst_json_file = root_dir / "utils/scripts/spec.json"
    
    print(json_file)

    if not json_file.is_file():
        print(f"[ERROR] JSON spec not found: {json_file}")
        return 1

    dst_json_file.write_bytes(json_file.read_bytes())
    
    print(dst_json_file)

    spec_hash = hashlib.md5(dst_json_file.read_text(encoding="utf-8").encode("utf-8")).hexdigest()    

    print(f"Computed MD5 hash: {spec_hash}")

    upload_to_s3("spec.json", bucket_name, repo_name, spec_hash)

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