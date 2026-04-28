"""ROM verification utilities for Pokemon FireRed (BPRE v1.0)."""

import hashlib
import sys

from offsets import TARGET_SHA1, ROM_NAME


def compute_sha1(path: str) -> str:
    """Return the hex-encoded SHA-1 digest of the file at *path*."""
    sha1 = hashlib.sha1()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            sha1.update(chunk)
    return sha1.hexdigest().upper()


def verify_rom(path: str) -> bool:
    """Check SHA-1 of *path* against the expected FireRed digest.

    Prints a pass/fail message and returns True if the ROM matches.
    """
    print(f"Verifying ROM: {path}")
    try:
        actual = compute_sha1(path)
    except FileNotFoundError:
        print(f"  ERROR: File not found: {path}")
        return False
    except OSError as exc:
        print(f"  ERROR: Could not read file: {exc}")
        return False

    if actual == TARGET_SHA1.upper():
        print(f"  PASS  SHA-1 matches {ROM_NAME}")
        print(f"        {actual}")
        return True
    else:
        print("  FAIL  SHA-1 mismatch!")
        print(f"        Expected : {TARGET_SHA1.upper()}")
        print(f"        Got      : {actual}")
        print(f"  Make sure you are using an unmodified {ROM_NAME} ROM.")
        return False


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python verify.py <rom_path>")
        print(f"Expected ROM : {ROM_NAME}")
        print(f"Expected SHA1: {TARGET_SHA1}")
        sys.exit(1)

    rom_path = sys.argv[1]
    ok = verify_rom(rom_path)
    sys.exit(0 if ok else 1)
