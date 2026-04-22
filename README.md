# GCS-UP

A professional GCS uploader that handles encrypted keys automatically. 

## Installation
```bash
git clone https://github.com/krisrowe/remote-gcs
cd remote-gcs
pipx install .
```

## Usage
The tool defaults to stateless mode. You must provide `--key` and `--bucket`.

### 1. Stateless Mode (No data saved)
```bash
gcs-up my-file.md --key my-access.txt --bucket my-bucket
```

### 2. Cached Mode (Optional)
On your main machine, you can enable caching to save typing. This uses `XDG_CACHE_HOME` (usually `~/.cache/remote-gcs/`).

**Enable Caching:**
```bash
gcs-up config enable --key my-access.txt --bucket my-bucket
```

**Simplified Usage (Once cached):**
```bash
gcs-up my-file.md
```

**Check Settings:**
```bash
gcs-up info
```

**Disable & Wipe Cache:**
```bash
gcs-up config disable
```

## Transport Security
If your key is an encrypted `.txt` file, the tool will automatically prompt for the passphrase at upload time.

**Transport Command:**
```bash
# Encrypt your key for transport
openssl enc -aes-256-cbc -pbkdf2 -salt -a -in sa.json -out my-access.txt
```

## Security
- **Strict Isolation**: Cache is only used if explicitly enabled via `config enable`.
- **Ephemeral Keys**: Decrypted JSON is stored in secure temporary files and deleted immediately after use.
