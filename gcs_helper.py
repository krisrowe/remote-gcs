import argparse
import os
import subprocess
import sys
import json
import getpass
import tempfile
import atexit

def decrypt_key(encrypted_path):
    print(f"Key '{encrypted_path}' appears to be encrypted.")
    pw = getpass.getpass("Enter decryption passphrase: ")
    
    # Create a secure temp file for the decrypted JSON
    fd, temp_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    
    # Register cleanup to ensure the plain JSON is deleted on exit
    atexit.register(lambda: os.path.exists(temp_path) and os.remove(temp_path))

    try:
        # Decrypt using openssl
        cmd = f"openssl enc -aes-256-cbc -pbkdf2 -salt -a -d -in {encrypted_path} -out {temp_path} -pass pass:{pw}"
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        return temp_path
    except subprocess.CalledProcessError:
        print("Error: Decryption failed. Check your passphrase.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="GCS Up - The simple uploader")
    parser.add_argument("file", help="File to upload")
    parser.add_argument("--key", required=True, help="Path to Service Account (JSON or encrypted .txt)")
    parser.add_argument("--bucket", required=True, help="GCS bucket name")
    
    args = parser.parse_args()

    # Automatic Decryption Logic
    actual_key = args.key
    if args.key.endswith(".txt") or ".txt" in args.key:
        actual_key = decrypt_key(args.key)

    # Perform the upload
    print(f"Uploading {args.file} to gs://{args.bucket}...")
    
    if subprocess.run("which gcloud", shell=True, capture_output=True).returncode == 0:
        # Use gcloud if present
        subprocess.run(f"gcloud auth activate-service-account --key-file={actual_key}", shell=True, check=True, capture_output=True)
        subprocess.run(f"gcloud storage cp {args.file} gs://{args.bucket}/", shell=True, check=True)
        print("Success!")
    else:
        # Fallback to python library
        try:
            from google.cloud import storage
            client = storage.Client.from_service_account_json(actual_key)
            b = client.bucket(args.bucket)
            b.blob(os.path.basename(args.file)).upload_from_filename(args.file)
            print("Success!")
        except ImportError:
            print("Error: Neither gcloud nor 'google-cloud-storage' found.")
            sys.exit(1)

if __name__ == "__main__":
    main()
