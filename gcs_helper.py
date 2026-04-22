import argparse
import os
import subprocess
import sys
import json
import getpass
import tempfile
import atexit
import shutil

# XDG Cache Handling
CACHE_DIR = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
APP_CACHE_DIR = os.path.join(CACHE_DIR, "remote-gcs")
CONFIG_PATH = os.path.join(APP_CACHE_DIR, "config.json")

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_config(config_dict):
    os.makedirs(APP_CACHE_DIR, exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config_dict, f, indent=2)

def wipe_cache():
    if os.path.exists(APP_CACHE_DIR):
        shutil.rmtree(APP_CACHE_DIR)
        print("Cache disabled and all settings removed.")
    else:
        print("Cache is already empty/disabled.")

def decrypt_key(encrypted_path):
    print(f"Key '{encrypted_path}' appears to be encrypted.")
    pw = getpass.getpass("Enter decryption passphrase: ")
    fd, temp_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    atexit.register(lambda: os.path.exists(temp_path) and os.remove(temp_path))
    try:
        cmd = f"openssl enc -aes-256-cbc -pbkdf2 -salt -a -d -in {encrypted_path} -out {temp_path} -pass pass:{pw}"
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        return temp_path
    except subprocess.CalledProcessError:
        print("Error: Decryption failed. Check your passphrase.")
        sys.exit(1)

def do_upload(file_path, key_path, bucket):
    actual_key = key_path
    if key_path.endswith(".txt") or ".txt" in key_path:
        actual_key = decrypt_key(key_path)

    print(f"Uploading {file_path} to gs://{bucket}...")
    if subprocess.run("which gcloud", shell=True, capture_output=True).returncode == 0:
        subprocess.run(f"gcloud auth activate-service-account --key-file={actual_key}", shell=True, check=True, capture_output=True)
        subprocess.run(f"gcloud storage cp {file_path} gs://{bucket}/", shell=True, check=True)
        print("Success!")
    else:
        try:
            from google.cloud import storage
            client = storage.Client.from_service_account_json(actual_key)
            b = client.bucket(bucket)
            b.blob(os.path.basename(file_path)).upload_from_filename(file_path)
            print("Success!")
        except ImportError:
            print("Error: Neither gcloud nor 'google-cloud-storage' found.")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(prog="gcs-up", description="GCS Up - Portable uploader with optional XDG caching")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # Upload command (default)
    up_parser = subparsers.add_parser("upload", help="Upload a file to GCS")
    up_parser.add_argument("file", help="File to upload")
    up_parser.add_argument("--key", help="Path to Service Account (JSON or encrypted .txt)")
    up_parser.add_argument("--bucket", help="GCS bucket name")

    # Config command
    conf_parser = subparsers.add_parser("config", help="Manage local caching/settings")
    conf_sub = conf_parser.add_subparsers(dest="subcommand", help="Config actions")
    
    enable_parser = conf_sub.add_parser("enable", help="Enable caching and save settings")
    enable_parser.add_argument("--key", required=True, help="Service Account key path")
    enable_parser.add_argument("--bucket", required=True, help="Target GCS bucket")
    
    conf_sub.add_parser("disable", help="Disable caching and wipe saved settings")

    # Info command
    subparsers.add_parser("info", help="Show current cached settings")

    # Handle default 'upload' if no subcommand provided but a file is present
    if len(sys.argv) > 1 and sys.argv[1] not in ["upload", "config", "info", "-h", "--help"]:
        sys.argv.insert(1, "upload")

    args = parser.parse_args()
    config = load_config()

    if args.command == "config":
        if args.subcommand == "enable":
            save_config({"key": os.path.abspath(args.key), "bucket": args.bucket, "cache_enabled": True})
            print(f"Caching enabled. Settings saved to {CONFIG_PATH}")
        elif args.subcommand == "disable":
            wipe_cache()
    
    elif args.command == "info":
        if not config.get("cache_enabled"):
            print("Caching is disabled.")
        else:
            print(f"Caching Enabled (XDG_CACHE_HOME: {APP_CACHE_DIR})")
            print(f"Bucket: {config.get('bucket')}")
            print(f"Key Path: {config.get('key')}")

    elif args.command == "upload":
        key = args.key or config.get("key")
        bucket = args.bucket or config.get("bucket")
        
        if not key or not bucket:
            print("Error: Missing key or bucket. Provide via args or run 'gcs-up config enable'.")
            sys.exit(1)
        
        do_upload(args.file, key, bucket)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
