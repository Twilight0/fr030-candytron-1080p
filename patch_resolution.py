#!/usr/bin/env python3
"""Patch the unpacked fr-030: Candytron executable to any custom resolution."""

import argparse
from pathlib import Path
import struct

# File offsets in the unpacked PE32 (.text mapped at 0x410000, raw offset 0x1000)
HEIGHT_OFFSETS = (
    (0x21D5, 0x68),  # 0x4111d4: push nHeight (CreateWindowExA)
    (0x29E7, 0xB8),  # 0x4119e6: mov eax, BackBufferHeight (D3DPRESENT_PARAMETERS)
)
WIDTH_OFFSETS = (
    (0x21DA, 0x68),  # 0x4111d9: push nWidth (CreateWindowExA)
    (0x29E2, 0xB9),  # 0x4119e1: mov ecx, BackBufferWidth (D3DPRESENT_PARAMETERS)
)


def patch_resolution(input_path: Path, output_path: Path, width: int, height: int) -> tuple[int, int]:
    """Validate expected opcodes and patch width/height immediates in-place."""
    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be positive integers.")

    data = bytearray(input_path.read_bytes())
    if data[:2] != b"MZ" or len(data) < 0x3000:
        raise ValueError(f"{input_path} does not look like the unpacked Candytron PE32 executable.")

    old_widths = set()
    for off, opcode in WIDTH_OFFSETS:
        if data[off - 1] != opcode:
            raise ValueError(f"Unexpected opcode at {off - 1:#x}: {data[off - 1]:#x} != {opcode:#x}")
        old_widths.add(struct.unpack_from("<I", data, off)[0])
        struct.pack_into("<I", data, off, width)

    old_heights = set()
    for off, opcode in HEIGHT_OFFSETS:
        if data[off - 1] != opcode:
            raise ValueError(f"Unexpected opcode at {off - 1:#x}: {data[off - 1]:#x} != {opcode:#x}")
        old_heights.add(struct.unpack_from("<I", data, off)[0])
        struct.pack_into("<I", data, off, height)

    if len(old_widths) != 1 or len(old_heights) != 1:
        raise ValueError(f"Inconsistent existing resolution in {input_path}: {old_widths} x {old_heights}")

    output_path.write_bytes(data)
    return next(iter(old_widths)), next(iter(old_heights))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Repatch fr030-candytron-final-101-1080p.exe to a custom fullscreen resolution (e.g. 3840 2160 for 4K)."
    )
    parser.add_argument("input", type=Path, help="Path to the unpacked Candytron executable")
    parser.add_argument("width", type=int, help="Target width in pixels (e.g. 3840)")
    parser.add_argument("height", type=int, help="Target height in pixels (e.g. 2160)")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output executable path (default: <stem>-<width>x<height>.exe)",
    )
    args = parser.parse_args()

    out = args.output or args.input.with_name(f"{args.input.stem}-{args.width}x{args.height}.exe")
    old_w, old_h = patch_resolution(args.input, out, args.width, args.height)
    print(f"Patched {old_w}x{old_h} -> {args.width}x{args.height}: {out}")


if __name__ == "__main__":
    main()
