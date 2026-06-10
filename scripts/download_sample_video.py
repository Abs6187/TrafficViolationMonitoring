"""
Download a single sample video from the DeepBug/RideSafe-400 HuggingFace dataset
using HTTP range requests — avoids downloading the full 4.8GB zip.

Output: frontend/public/sample_demo.mp4
"""

import io
import os
import struct
import sys

import requests

TOKEN = os.getenv("HF_TOKEN", "")
if not TOKEN:
    print("ERROR: Set the HF_TOKEN environment variable before running this script.")
    print("  Windows PowerShell: $env:HF_TOKEN='hf_...'")
    print("  Linux/Mac:          export HF_TOKEN='hf_...'")
    sys.exit(1)
DATASET_URL = (
    "https://huggingface.co/datasets/DeepBug/RideSafe-400"
    "/resolve/main/videoset1_videos_part1.zip"
)
TOTAL_SIZE = 4_821_773_616  # from Content-Length header
OUT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "frontend", "public", "sample_demo.mp4"
)

AUTH = {"Authorization": f"Bearer {TOKEN}"}


def range_get(url: str, start: int, end: int) -> bytes:
    r = requests.get(url, headers={**AUTH, "Range": f"bytes={start}-{end}"}, timeout=60)
    r.raise_for_status()
    return r.content


def find_zip64_cd_info() -> tuple[int, int, int]:
    """Return (cd_offset, cd_size, num_entries) from ZIP64 EOCD structures."""
    # Grab the last 64KB which always contains EOCD / ZIP64 locator
    tail = range_get(DATASET_URL, TOTAL_SIZE - 65536, TOTAL_SIZE - 1)

    # ZIP64 End of Central Directory Locator  PK 06 07
    loc_sig = b"PK\x06\x07"
    loc_idx = tail.rfind(loc_sig)
    if loc_idx == -1:
        raise RuntimeError("ZIP64 locator not found — may not be a zip64 archive")

    _disk_with_z64, z64_eocd_offset, _total_disks = struct.unpack_from(
        "<IQI", tail, loc_idx + 4
    )
    print(f"ZIP64 EOCD offset: {z64_eocd_offset}")

    # ZIP64 End of Central Directory Record  PK 06 06
    z64_eocd_data = range_get(DATASET_URL, z64_eocd_offset, z64_eocd_offset + 56)
    (
        _sig,
        _size_of_record,
        _ver_made,
        _ver_need,
        _disk_num,
        _disk_cd,
        _entries_disk,
        total_entries,
        cd_size,
        cd_offset,
    ) = struct.unpack_from("<4sQHHIIQQQQ", z64_eocd_data)
    print(f"Central Directory: offset={cd_offset}, size={cd_size}, entries={total_entries}")
    return cd_offset, cd_size, total_entries


def list_entries(cd_offset: int, cd_size: int):
    """Parse central directory and return list of entry dicts."""
    cd_data = range_get(DATASET_URL, cd_offset, cd_offset + cd_size - 1)
    entries = []
    pos = 0
    while pos < len(cd_data):
        if cd_data[pos : pos + 4] != b"PK\x01\x02":
            break
        # 46-byte fixed header
        (
            _ver_made, _ver_need, _flag, _comp_method, _mod_time, _mod_date,
            _crc32, comp_size, uncomp_size,
            fname_len, extra_len, comment_len,
            _disk_start, _int_attrs, _ext_attrs,
        ) = struct.unpack_from("<HHHHHHIIIHHHHHI", cd_data, pos + 4)

        local_offset_raw = struct.unpack_from("<I", cd_data, pos + 42)[0]
        fname = cd_data[pos + 46 : pos + 46 + fname_len].decode("utf-8", errors="replace")

        # Parse ZIP64 extra field if needed
        local_offset = local_offset_raw
        extra_start = pos + 46 + fname_len
        extra_end = extra_start + extra_len
        ex = cd_data[extra_start:extra_end]
        ex_pos = 0
        while ex_pos + 4 <= len(ex):
            tag, size = struct.unpack_from("<HH", ex, ex_pos)
            if tag == 0x0001:  # ZIP64 extended info
                vals = struct.unpack_from("<" + "Q" * (size // 8), ex, ex_pos + 4)
                idx = 0
                if uncomp_size == 0xFFFFFFFF:
                    uncomp_size = vals[idx]; idx += 1
                if comp_size == 0xFFFFFFFF:
                    comp_size = vals[idx]; idx += 1
                if local_offset_raw == 0xFFFFFFFF and idx < len(vals):
                    local_offset = vals[idx]
            ex_pos += 4 + size

        entries.append({
            "name": fname,
            "comp_size": comp_size,
            "uncomp_size": uncomp_size,
            "local_offset": local_offset,
        })
        pos += 46 + fname_len + extra_len + comment_len

    return entries


def extract_entry(entry: dict, out_path: str):
    """Download and decompress a single zip entry via HTTP range."""
    import zlib

    offset = entry["local_offset"]
    # Read local file header (30 bytes + variable)
    lh_data = range_get(DATASET_URL, offset, offset + 299)
    if lh_data[:4] != b"PK\x03\x04":
        raise RuntimeError("Local file header signature mismatch")
    fname_len, extra_len = struct.unpack_from("<HH", lh_data, 26)
    data_start = offset + 30 + fname_len + extra_len
    comp_size = entry["comp_size"]
    comp_method = struct.unpack_from("<H", lh_data, 8)[0]

    print(f"Downloading {comp_size // 1024 // 1024} MB of compressed data...")
    chunk_size = 4 * 1024 * 1024  # 4 MB chunks
    compressed = b""
    downloaded = 0
    while downloaded < comp_size:
        end = min(data_start + downloaded + chunk_size - 1, data_start + comp_size - 1)
        chunk = range_get(DATASET_URL, data_start + downloaded, end)
        compressed += chunk
        downloaded += len(chunk)
        pct = downloaded * 100 // comp_size
        print(f"  {pct}% ({downloaded // 1024 // 1024} MB / {comp_size // 1024 // 1024} MB)", end="\r")

    print()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    if comp_method == 0:  # stored (no compression)
        with open(out_path, "wb") as f:
            f.write(compressed)
    elif comp_method == 8:  # deflate
        decompressed = zlib.decompress(compressed, -15)
        with open(out_path, "wb") as f:
            f.write(decompressed)
    else:
        raise RuntimeError(f"Unsupported compression method: {comp_method}")

    print(f"Saved to: {out_path}  ({os.path.getsize(out_path) // 1024 // 1024} MB)")


def main():
    print("=== RideSafe-400 Sample Video Downloader ===")
    cd_offset, cd_size, num_entries = find_zip64_cd_info()
    print(f"Parsing {num_entries} entries...")
    entries = list_entries(cd_offset, cd_size)

    print(f"\nAll files in archive ({len(entries)} total):")
    for i, e in enumerate(entries):
        mb = e["comp_size"] // 1024 // 1024
        print(f"  [{i:2d}] {e['name']}  {mb} MB  offset={e['local_offset']}")

    # Pick the smallest mp4 for demo
    mp4s = [e for e in entries if e["name"].lower().endswith(".mp4")]
    if not mp4s:
        print("No .mp4 files found!")
        sys.exit(1)

    target = min(mp4s, key=lambda e: e["comp_size"])
    print(f"\nSelected smallest video: {target['name']} ({target['comp_size'] // 1024 // 1024} MB compressed)")

    out = os.path.abspath(OUT_PATH)
    extract_entry(target, out)
    print("\nDone!")


if __name__ == "__main__":
    main()
