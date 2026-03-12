# Reverb Auto-Relister

Automatically relists sold items on your Reverb store. Built for "unlimited supply" storefronts (3D-printed products, etc.) where each sale ends the listing even though you have infinite stock.

**Zero dependencies** — runs on any machine with Python 3.7+.

## How It Works

1. Polls your Reverb shop for sold listings
2. Copies all details (title, description, photos, price, shipping, etc.)
3. Creates a new identical listing and publishes it immediately
4. Tracks what's been relisted so it never duplicates

## Setup

### 1. Get a Reverb API Token

Go to [https://reverb.com/my/api_settings](https://reverb.com/my/api_settings) and generate a Personal Access Token.

### 2. Configure

```bash
cp config.example.json config.json
# Edit config.json — add your API token
```

### 3. Test with Dry Run

```bash
python3 reverb-relister.py --dry-run
```

This shows what *would* be relisted without actually creating anything.

### 4. Run for Real

```bash
python3 reverb-relister.py
```

## Running on a Schedule

### macOS (launchd)

```bash
# Create a plist that runs every 15 minutes
cat > ~/Library/LaunchAgents/com.reverb-relister.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.reverb-relister</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/reverb-relister.py</string>
    </array>
    <key>StartInterval</key>
    <integer>900</integer>
    <key>StandardOutPath</key>
    <string>/tmp/reverb-relister.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/reverb-relister.log</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.reverb-relister.plist
```

### Linux (cron)

```bash
# Run every 15 minutes
crontab -e
# Add: */15 * * * * cd /path/to/reverb-relister && python3 reverb-relister.py
```

### Windows (Task Scheduler)

```powershell
# Run every 15 minutes
schtasks /create /tn "ReverbRelister" /tr "python3 C:\path\to\reverb-relister.py" /sc minute /mo 15
```

## Configuration

| Field | Default | Description |
|-------|---------|-------------|
| `api_token` | *required* | Your Reverb Personal Access Token |
| `dry_run` | `false` | Preview mode — logs what would happen |
| `default_inventory` | `1` | Inventory count for new listings |
| `initial_lookback_days` | `30` | How far back to look on first run |
| `sku_allowlist` | `null` | List of SKUs to relist. `null` = relist all sold items |

## Files

| File | Purpose |
|------|---------|
| `reverb-relister.py` | The script |
| `config.json` | Your config (gitignored) |
| `config.example.json` | Template config |
| `state.json` | Tracks relisted items (auto-created) |
| `relister.log` | Activity log |

## Commands

```bash
python3 reverb-relister.py              # Run the relister
python3 reverb-relister.py --dry-run    # Preview without creating listings
python3 reverb-relister.py --reset      # Reset state (reprocess all sold items)
python3 reverb-relister.py --help       # Show help
```

## Notes

- Reverb API tokens don't expire
- The script is idempotent — safe to run repeatedly
- Photos are copied by URL reference (Reverb hosts them)
- Rate limited internally (0.5-1s between API calls)
- State file prevents double-relisting across runs
