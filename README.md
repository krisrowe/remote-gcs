# RGCS - Remote GCS Utility

A conventional, portable CLI for transferring files to/from Google Cloud Storage with automatic key decryption.

## Installation
```bash
git clone https://github.com/krisrowe/remote-gcs
pipx install ./remote-gcs
```

## Setup (Optional Caching)
Enable caching to store your bucket name and key path in `XDG_CACHE_HOME`.
```bash
rgcs config enable --key my-access.txt --bucket my-bucket
```

## Usage

### Upload a file
```bash
rgcs put my-file.md
# (If not cached)
rgcs put my-file.md --key my-access.txt --bucket my-bucket
```

### Download a file
```bash
rgcs get remote-file.txt
```

### Check Status / Wipe Cache
```bash
rgcs info
rgcs config disable
```

## Transport Security
If your key is an encrypted `.txt` file, `rgcs` will automatically prompt for the passphrase.

**To create a transport file:**
```bash
openssl enc -aes-256-cbc -pbkdf2 -salt -a -in sa.json -out my-access.txt
```

## Security
- **No default persistence**: Settings are only saved if `config enable` is called.
- **Secure cleanup**: Decrypted JSON keys are stored in temp files and deleted immediately after the operation.
