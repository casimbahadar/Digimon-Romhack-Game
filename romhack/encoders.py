"""FireRed text encoding/decoding utilities.

FireRed uses a custom character set where:
  Space  = 0xFC
  .      = 0xAD
  !      = 0xAB
  '      = 0xB4
  -      = 0xAE
  A–Z    = 0xBB – 0xD4
  a–z    = 0xD5 – 0xEE
  0–9    = 0xA1 – 0xAA
  End    = 0xFF  (terminator)
"""

# ---------------------------------------------------------------------------
# Character set
# ---------------------------------------------------------------------------

FIRERED_CHARSET: dict[str, int] = {
    " ": 0xFC,
    ".": 0xAD,
    "!": 0xAB,
    "'": 0xB4,
    "-": 0xAE,
    "?": 0xAC,
    "/": 0xBA,
    ",": 0xB8,
    ":": 0xF0,
    ";": 0xF1,
    "(": 0xB9,
    ")": 0xBA,
    "&": 0xB5,
    "%": 0xB7,
}

# A–Z  →  0xBB – 0xD4
for _i, _ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
    FIRERED_CHARSET[_ch] = 0xBB + _i

# a–z  →  0xD5 – 0xEE
for _i, _ch in enumerate("abcdefghijklmnopqrstuvwxyz"):
    FIRERED_CHARSET[_ch] = 0xD5 + _i

# 0–9  →  0xA1 – 0xAA
for _i, _ch in enumerate("0123456789"):
    FIRERED_CHARSET[_ch] = 0xA1 + _i

# Terminator constant
TERMINATOR: int = 0xFF
_FALLBACK: int = 0xFC  # space used for unknown characters

# Build reverse mapping once
_REVERSE_CHARSET: dict[int, str] = {v: k for k, v in FIRERED_CHARSET.items()}
_REVERSE_CHARSET[TERMINATOR] = ""  # terminator maps to empty string


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def encode_name(name: str, max_len: int = 10) -> bytes:
    """Encode *name* to FireRed bytes.

    The result is exactly *max_len* + 1 bytes:
      - The first *max_len* bytes are the encoded characters (truncated or
        space-padded with 0xFC if the name is shorter).
      - The final byte is the 0xFF terminator.

    Unknown characters are substituted with 0xFC (space).
    """
    encoded = bytearray()
    for ch in name[:max_len]:
        encoded.append(FIRERED_CHARSET.get(ch, _FALLBACK))

    # Pad with spaces (0xFC) up to max_len
    while len(encoded) < max_len:
        encoded.append(_FALLBACK)

    encoded.append(TERMINATOR)
    return bytes(encoded)


def encode_text(text: str, max_len: int = 255) -> bytes:
    """Encode *text* to FireRed bytes, terminated with 0xFF.

    Unlike encode_name, this does *not* pad — it simply truncates at
    *max_len* characters and appends the terminator.  Returns at most
    *max_len* + 1 bytes.
    """
    encoded = bytearray()
    for ch in text[:max_len]:
        encoded.append(FIRERED_CHARSET.get(ch, _FALLBACK))
    encoded.append(TERMINATOR)
    return bytes(encoded)


def decode_name(data: bytes) -> str:
    """Reverse of encode_name.

    Decodes FireRed bytes back to a Python string, stopping at the first
    0xFF terminator (or end of *data*).  Unknown byte values are replaced
    with '?'.
    """
    result = []
    for byte in data:
        if byte == TERMINATOR:
            break
        result.append(_REVERSE_CHARSET.get(byte, "?"))
    return "".join(result).rstrip()
