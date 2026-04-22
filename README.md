# GCS-UP

A dead-simple GCS uploader that handles encrypted keys automatically. No data is stored locally.

## Installation
```bash
git clone https://github.com/krisrowe/remote-gcs
cd remote-gcs
pipx install .
```

## Usage
Provide the key path and bucket name for every upload. 

### With a standard JSON key:
```bash
gcs-up my-file.md --key sa.json --bucket my-bucket
```

### With an encrypted key:
If your key ends in `.txt`, the tool automatically prompts for the passphrase.
```bash
gcs-up my-file.md --key my-access.txt --bucket my-bucket
# Key 'my-access.txt' appears to be encrypted.
# Enter decryption passphrase: 
# Uploading my-file.md to gs://my-bucket...
# Success!
```

## Security
- **No Persistence**: This tool does not save your key path or bucket name.
- **Secure Decryption**: Decrypted keys are stored in temporary files and deleted immediately after upload.
- **Transport**: Uses `openssl` (AES-256-CBC) for decryption.
