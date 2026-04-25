# Digimon FireRed ROM Hack Patcher

Replaces all 200 Pokemon in FireRed with Digimon — names and base stats.

## Requirements
- Python 3.8+
- A legal copy of **Pokemon FireRed (BPRE v1.0)**
  - SHA-1: `DD5945DB9B930750CB39D00C84DA8571FEEBF417`

## Usage

### Patch ROM directly
```bash
python patcher.py firered.gba
# Outputs: firered_digimon.gba
```

### Generate IPS patch only
```bash
python patcher.py firered.gba --patch-only
# Outputs: firered_digimon.ips
```

Apply the IPS patch with [Lunar IPS](https://fusoya.eludevisibility.org/lips/) or any compatible patcher.

## Disclaimer
This tool requires your own legally obtained ROM. No ROM files are distributed here.
