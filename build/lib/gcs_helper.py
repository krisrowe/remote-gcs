import argparse
import os
import subprocess
import sys
import json
import getpass
import tempfile
import atexit
import shutil

CACHE_DIR = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
APP_CACHE_DIR = os.path.join(CACHE_DIR, "rgcs")
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
        print("Cache disabled and settings removed.")
    else:
        print("Cache is already empty.")

def decrypt_key(encrypted_path):
    print(f"Key '{encrypted_path}' appears to be encrypted.")
    # Check if we have a password on stdin or need to prompt
    if not sys.stdin.isatty():
        pw = sys.stdin.readline().strip()
    else:
        pw = getpass.getpass("Enter decryption passphrase: ")
    
    fd, temp_path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    atexit.register(lambda: os.path.exists(temp_path) and os.remove(temp_path))
    try:
        # Use -pass pass: for scripting, or it might hang
        cmd = ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt", "-a", "-d", "-in", encrypted_path, "-out", temp_path, "-pass", f"pass:{pw}"]
        subprocess.run(cmd, check=True, capture_output=True)
        return temp_path
    except subprocess.CalledProcessError as e:
        print(f"Error: Decryption failed. {e.stderr.decode() if e.stderr else ''}")
        sys.exit(1)

def get_client(key_path):
    actual_key = key_path
    if key_path.endswith(".txt") or ".txt" in key_path:
        actual_key = decrypt_key(key_path)
    
    if subprocess.run("which gcloud", shell=True, capture_output=True).returncode == 0:
        subprocess.run(f"gcloud auth activate-service-account --key-file={actual_key}", shell=True, check=True, capture_output=True)
        return "gcloud"
    else:
        try:
            from google.cloud import storage
            return storage.Client.from_service_account_json(actual_key)
        except ImportError:
            print("Error: Neither gcloud nor 'google-cloud-storage' found.")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(prog="rgcs")
    subparsers = parser.add_subparsers(dest="command")

    put_parser = subparsers.add_parser("put")
    put_parser.add_argument("file")
    put_parser.add_argument("--key")
    put_parser.add_argument("--bucket")

    get_parser = subparsers.add_parser("get")
    get_parser.add_argument("file")
    get_parser.add_argument("--key")
    get_parser.add_argument("--bucket")

    conf_parser = subparsers.add_parser("config")
    conf_sub = conf_parser.add_subparsers(dest="subcommand")
    enable_parser = conf_sub.add_parser("enable")
    enable_parser.add_argument("--key", required=True)
    enable_parser.add_argument("--bucket", required=True)
    conf_sub.add_parser("disable")

    subparsers.add_parser("info")

    args = parser.parse_args()
    config = load_config()

    if args.command == "config":
        if args.subcommand == "enable":
            save_config({"key": os.path.abspath(args.key), "bucket": args.bucket, "cache_enabled": True})
            print(f"Config saved.")
        elif args.subcommand == "disable":
            wipe_cache()
    elif args.command == "info":
        if not config.get("cache_enabled"):
            print("Caching disabled.")
        else:
            print(f"Bucket: {config.get('bucket')}\nKey: {config.get('key')}")
    elif args.command in ["put", "get"]:
        key = args.key or config.get("key")
        bucket = args.bucket or config.get("bucket")
        if not key or not bucket:
            print("Error: Missing config.")
            sys.exit(1)
        client = get_client(key)
        if args.command == "put":
            if client == "gcloud":
                subprocess.run(f"gcloud storage cp {args.file} gs://{bucket}/", shell=True, check=True)
            else:
                client.bucket(bucket).blob(os.path.basename(args.file)).upload_from_filename(args.file)
            print(f"Uploaded {args.file}")
        else:
            if client == "gcloud":
                subprocess.run(f"gcloud storage cp gs://{bucket}/{args.file} .", shell=True, check=True)
            else:
                client.bucket(bucket).blob(args.file).download_to_filename(args.file)
            print(f"Downloaded {args.file}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
