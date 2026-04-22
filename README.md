# GCS-UP

A dead-simple GCS uploader that handles encrypted keys automatically.

## Installation
```bash
git clone https://github.com/krisrowe/remote-gcs
cd remote-gcs
pipx install .
```

## Setup (One-time)
Tell the tool where your key is and which bucket to use.
```bash
gcs-up --config
```
*Note: You can point it to a `.json` key or an encrypted `.txt` key.*

## Usage
If your key is a `.json`, it just works:
```bash
gcs-up my-file.md
```

If your key is an encrypted `.txt`, it will prompt you:
```bash
gcs-up my-file.md
# Key 'my-access.txt' appears to be encrypted.
# Enter decryption passphrase: 
# Uploading my-file.md to gs://my-bucket...
# Success!
```

## Security
- Decrypted keys are stored in memory/temporary files and deleted immediately after upload.
- Uses `openssl` (AES-256-CBC) for decryption.
