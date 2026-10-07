#!/usr/bin/env python3
"""
Script to extract IPs and URLs from Microsoft 365 JSON endpoint data.
Writes IPv4 addresses and FQDN to the files configured below.
"""

import ipaddress
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Set

# Hostname, or a single leading "*." wildcard. Rejects partial and mid-name wildcards.
_FQDN_PATTERN = re.compile(
    r"^(?:\*\.)?(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Configuration
# Edit these values before running the script.
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path("data/")
IPS_FILENAME = "snwl365.txt"
FQDN_FILENAME = "snwl365-fqdn.txt"
# Give up on the download if the endpoint does not respond in time.
REQUEST_TIMEOUT_SECONDS = 60


def download_json(url: str) -> Any:
    """Download JSON from URL."""
    try:
        with urllib.request.urlopen(url, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            payload = response.read()
        return json.loads(payload.decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeError) as e:
        print(f"Error downloading JSON from URL: {e}", file=sys.stderr)
        sys.exit(1)


def load_json_from_file(filepath: str) -> Any:
    """Load JSON from a local file."""
    try:
        with open(filepath, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError, UnicodeError) as e:
        print(f"Error reading JSON file: {e}", file=sys.stderr)
        sys.exit(1)


def is_valid_ip(ip: str) -> bool:
    """
    Validate IP: only IPv4 addresses are allowed (with or without CIDR notation).
    IPv6 addresses (containing ':') are excluded.
    
    Examples:
    - '192.168.1.1' -> valid
    - '192.168.1.0/24' -> valid
    - '2603:1006::/40' -> invalid (IPv6)
    - '2620:1ec:4::152/128' -> invalid (IPv6)
    """
    value = ip.strip()
    if not value:
        return False

    # IPv4Network accepts a bare address as a /32 and rejects IPv6.
    # strict=False keeps prefixes whose host bits are set.
    try:
        ipaddress.IPv4Network(value, strict=False)
    except ValueError:
        return False
    return True


def is_valid_url(url: str) -> bool:
    """
    Validate URL: asterisks are only allowed at the beginning of the string
    in the format '*.domain.com'. Exclude wildcards in the middle or partial wildcards.
    
    Examples:
    - '*.microsoft.com' -> valid
    - '*cdn.onenote.net' -> invalid (partial wildcard)
    - 'autodiscover.*.onmicrosoft.com' -> invalid (wildcard in the middle)
    - 'example.com' -> valid (no wildcard)
    """
    value = url.strip()
    if not value or len(value) > 253:
        return False

    # The pattern allows only a leading "*." wildcard, so partial and mid-name
    # wildcards fail here along with schemes, paths, and spaces.
    return _FQDN_PATTERN.fullmatch(value) is not None


def extract_ips_and_urls(data: list) -> tuple[Set[str], Set[str]]:
    """Extract all unique IPs and URLs from JSON data."""
    ips = set()
    urls = set()
    
    for item in data:
        if isinstance(item, dict):
            # Extract IPs (with validation - only IPv4)
            if 'ips' in item and isinstance(item['ips'], list):
                for ip in item['ips']:
                    if isinstance(ip, str) and ip.strip():
                        if is_valid_ip(ip):
                            ips.add(ip.strip())
            
            # Extract URLs (with validation)
            if 'urls' in item and isinstance(item['urls'], list):
                for url in item['urls']:
                    if isinstance(url, str) and url.strip():
                        if is_valid_url(url):
                            urls.add(url.strip())
    
    return ips, urls


def stage_output(path: Path, items: Set[str]) -> Path:
    """Write sorted items to a temporary file next to the destination."""
    temporary = path.with_name(f".{path.name}.tmp")
    content = "".join(f"{item}\n" for item in sorted(items))
    try:
        temporary.write_text(content, encoding="utf-8")
    except OSError:
        temporary.unlink(missing_ok=True)
        raise
    return temporary


def publish_outputs(outputs: list[tuple[Path, Set[str]]]) -> None:
    """Replace every output file only after all temporary files are written."""
    staged: list[tuple[Path, Path]] = []
    try:
        for path, items in outputs:
            staged.append((stage_output(path, items), path))
        for temporary, path in staged:
            os.replace(temporary, path)
    except OSError as e:
        for temporary, _path in staged:
            temporary.unlink(missing_ok=True)
        print(f"Error writing output files: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main function."""
    # Check if URL or file path is provided as argument
    if len(sys.argv) > 1:
        source = sys.argv[1]
        # Treat only web URLs as remote sources. Match the scheme case-insensitively.
        if source.lower().startswith(("http://", "https://")):
            data = download_json(source)
        else:
            data = load_json_from_file(source)
    else:
        # Default to test.json stored beside this script, not the shell's working directory.
        default_file = Path(__file__).parent / "test.json"
        if default_file.exists():
            data = load_json_from_file(str(default_file))
        else:
            print("Usage: python parser.py [URL or file_path]", file=sys.stderr)
            print("Example: python parser.py https://endpoints.office.com/endpoints/worldwide", file=sys.stderr)
            sys.exit(1)
    
    # Validate data structure
    if not isinstance(data, list):
        print("Error: JSON data must be an array", file=sys.stderr)
        sys.exit(1)
    
    # Extract IPs and URLs
    ips, urls = extract_ips_and_urls(data)

    # An empty result usually means the feed changed shape or every value was rejected.
    # Leave the previous files in place so a published list is not wiped.
    if not ips or not urls:
        print(
            "Error: extraction produced an empty IP or FQDN list; existing output files were left unchanged.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        print(f"Error creating output directory: {e}", file=sys.stderr)
        sys.exit(1)

    ips_path = OUTPUT_DIR / IPS_FILENAME
    fqdn_path = OUTPUT_DIR / FQDN_FILENAME
    publish_outputs([(ips_path, ips), (fqdn_path, urls)])

    print(f"Extracted {len(ips)} unique IPs to {ips_path}")
    print(f"Extracted {len(urls)} unique URLs to {fqdn_path}")


if __name__ == '__main__':
    main()
