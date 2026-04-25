"""IPS (International Patching System) patch creation and application."""

import struct


class IpsPatch:
    """Represents an IPS patch file."""

    HEADER = b"PATCH"
    FOOTER = b"EOF"

    def __init__(self) -> None:
        self.records: list[tuple[int, bytes]] = []

    def add_record(self, offset: int, data: bytes) -> None:
        """Append a (offset, data) record to the patch."""
        self.records.append((offset, data))

    def _merge_records(self) -> list[tuple[int, bytes]]:
        """Merge contiguous or overlapping records into a single sorted list."""
        if not self.records:
            return []

        # Sort by offset
        sorted_records = sorted(self.records, key=lambda r: r[0])

        merged: list[tuple[int, bytes]] = []
        cur_offset, cur_data = sorted_records[0]
        cur_data = bytearray(cur_data)

        for offset, data in sorted_records[1:]:
            # Check if this record is contiguous with (or overlaps) the current one
            end_of_current = cur_offset + len(cur_data)
            if offset <= end_of_current:
                # Overlapping or contiguous: extend cur_data
                overlap = end_of_current - offset
                extension = data[overlap:] if overlap < len(data) else b""
                cur_data.extend(extension)
            else:
                # Gap: flush current and start a new one
                merged.append((cur_offset, bytes(cur_data)))
                cur_offset = offset
                cur_data = bytearray(data)

        merged.append((cur_offset, bytes(cur_data)))
        return merged

    def encode(self) -> bytes:
        """Return the full IPS binary: header + records + footer."""
        merged = self._merge_records()
        output = bytearray(self.HEADER)

        for offset, data in merged:
            if offset > 0xFFFFFF:
                raise ValueError(f"IPS offset 0x{offset:X} exceeds 24-bit maximum")

            # Split large records (IPS max record data size is 65535 bytes)
            pos = 0
            while pos < len(data):
                chunk = data[pos : pos + 0xFFFF]
                chunk_offset = offset + pos

                # 3-byte big-endian offset
                output += struct.pack(">I", chunk_offset)[1:]  # drop leading byte
                # 2-byte big-endian size
                output += struct.pack(">H", len(chunk))
                # raw data
                output += chunk
                pos += len(chunk)

        output += self.FOOTER
        return bytes(output)

    def save(self, path: str) -> None:
        """Write the encoded IPS patch to *path*."""
        with open(path, "wb") as fh:
            fh.write(self.encode())

    @staticmethod
    def load(path: str) -> "IpsPatch":
        """Read an IPS file from *path* and return an IpsPatch with its records."""
        patch = IpsPatch()
        with open(path, "rb") as fh:
            data = fh.read()

        if not data.startswith(IpsPatch.HEADER):
            raise ValueError("Not a valid IPS file: missing PATCH header")

        pos = len(IpsPatch.HEADER)
        while pos < len(data):
            # Check for EOF footer
            if data[pos : pos + 3] == IpsPatch.FOOTER:
                break

            if pos + 3 > len(data):
                raise ValueError("IPS file truncated while reading offset")

            offset = struct.unpack(">I", b"\x00" + data[pos : pos + 3])[0]
            pos += 3

            if pos + 2 > len(data):
                raise ValueError("IPS file truncated while reading size")

            size = struct.unpack(">H", data[pos : pos + 2])[0]
            pos += 2

            if size == 0:
                # RLE record: next 2 bytes are repeat count, then 1 byte value
                if pos + 3 > len(data):
                    raise ValueError("IPS file truncated while reading RLE record")
                rle_count = struct.unpack(">H", data[pos : pos + 2])[0]
                rle_byte = data[pos + 2 : pos + 3]
                pos += 3
                patch.add_record(offset, rle_byte * rle_count)
            else:
                if pos + size > len(data):
                    raise ValueError("IPS file truncated while reading record data")
                patch.add_record(offset, data[pos : pos + size])
                pos += size

        return patch

    def apply(self, rom_data: bytearray) -> bytearray:
        """Apply all patch records to *rom_data* and return the modified copy."""
        result = bytearray(rom_data)
        for offset, data in self.records:
            end = offset + len(data)
            # Extend ROM if necessary
            if end > len(result):
                result.extend(b"\xFF" * (end - len(result)))
            result[offset:end] = data
        return result
