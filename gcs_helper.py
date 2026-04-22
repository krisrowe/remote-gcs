import argparse
import os
import subprocess
import sys
import json
import getpass
import tempfile
import atexit

CONFIG_PATH = os.path.expanduser("~/.gcs_helper_config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_config(key_path, bucket):
    with open(CONFIG_PATH, 'w') as f:
        json.dump({"key": os.path.abspath(key_path), "bucket": bucket}, f)
    print(f"Config saved: {CONFIG_PATH}")

def decrypt_key(encrypted_path):
    print(f"Key '{encrypted_path}' appears to be encrypted.")
    pw = getpass.getpass("Enter decryption passphrase: ")
    
    # Create a secure temp file for the decrypted JSON
    fd, temp_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    
    # Register cleanup to ensure the plain JSON is deleted on exit
    atexit.register(lambda: os.path.exists(temp_path) and os.remove(temp_path))

    try:
        # Try to decrypt using the ubiquitous openssl command
        cmd = f"openssl enc -aes-256-cbc -pbkdf2 -salt -a -d -in {encrypted_path} -out {temp_path} -pass pass:{pw}"
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        return temp_path
    except subprocess.CalledProcessError:
        print("Error: Decryption failed. Check your passphrase.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="GCS Up - The simple uploader")
    parser.add_argument("file", nargs="?", help="File to upload")
    parser.add_argument("--config", action="store_true", help="Set default key and bucket")
    parser.add_argument("--bucket", help="Override bucket")
    
    args = parser.parse_args()
    config = load_config()

    if args.config:
        key_path = input("Path to Service Account (JSON or encrypted .txt): ").strip()
        bucket = input("GCS bucket name: ").strip()
        save_config(key_path, bucket)
        return

    key_path = config.get("key")
    bucket = args.bucket or config.get("bucket")

    if not key_path or not bucket:
        print("Error: Not configured. Run 'gcs-up --config' first.")
        sys.exit(1)

    if not args.file:
        print("Usage: gcs-up <file>")
        sys.exit(1)

    # Automatic Decryption Logic
    actual_key = key_path
    if key_path.endswith(".txt") or ".txt" in key_path:
        actual_key = decrypt_key(key_path)

    # Perform the upload
    print(f"Uploading {args.file} to gs://{bucket}...")
    
    if subprocess.run("which gcloud", shell=True, capture_output=True).returncode == 0:
        # Use gcloud if present
        subprocess.run(f"gcloud auth activate-service-account --key-file={actual_key}", shell=True, check=True, capture_output=True)
        subprocess.run(f"gcloud storage cp {args.file} gs://{bucket}/", shell=True, check=True)
        print("Success!")
    else:
        # Fallback to python library
        try:
            from google.cloud import storage
            client = storage.Client.from_service_account_json(actual_key)
            b = client.bucket(bucket)
            b.blob(os.path.basename(args.file)).upload_from_filename(args.file)
            print("Success!")
        except ImportError:
            print("Error: Neither gcloud nor 'google-cloud-storage' found.")
            sys.exit(1)

if __name__ == "__main__":
    main()
