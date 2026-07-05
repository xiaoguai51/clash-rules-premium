#!/usr/bin/env python3
"""
Shadowrocket ADBlock Rules → Clash Premium Rule Sets Converter

Downloads .conf files from the Shadowrocket-ADBlock-Rules-Forever project
(release branch), parses the [Rule] section, and generates Clash Premium
compatible rule sets in both .txt and .yaml formats.

Rule set behaviors:
  - domain    : pure domain list (DOMAIN / DOMAIN-SUFFIX)
  - ipcidr    : pure IP CIDR list (IP-CIDR / IP-CIDR6)
  - classical : mixed rule types with TYPE prefix (includes DOMAIN-KEYWORD)

Usage:
    python3 convert.py [--output-dir ../rules]

GitHub Actions runs this script weekly to keep rule sets up to date.
"""

import os
import sys
import json
import argparse
import subprocess
from datetime import datetime, timezone, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Shadowrocket project raw file base URL (release branch)
SR_BASE_URL = (
    "https://raw.githubusercontent.com/johnshall/"
    "Shadowrocket-ADBlock-Rules-Forever/release"
)

# Source .conf files and their purpose
#   adblock : sr_ad_only.conf          → all Reject rules (ad blocking only)
#   proxy   : sr_top500_banlist.conf   → Proxy rules (blacklist mode, no ad)
#   direct  : sr_top500_whitelist.conf → Direct rules (whitelist mode, no ad)
SR_FILES = {
    "sr_ad_only.conf": "adblock",
    "sr_top500_banlist.conf": "proxy",
    "sr_top500_whitelist.conf": "direct",
}

# Rule types recognised by Clash Premium
DOMAIN_TYPES = {"DOMAIN", "DOMAIN-SUFFIX"}
KEYWORD_TYPES = {"DOMAIN-KEYWORD"}
IP_TYPES = {"IP-CIDR", "IP-CIDR6"}

# Policy mapping (Shadowrocket policy → category)
REJECT_POLICIES = {"reject", "reject-no-drop", "reject-img", "reject-dict",
                   "reject-tun", "reject-proxy"}
PROXY_POLICIES = {"proxy"}
DIRECT_POLICIES = {"direct"}


# ---------------------------------------------------------------------------
# Network / file I/O
# ---------------------------------------------------------------------------

def download_file(url, dest_path):
    """
    Download *url* to *dest_path* using curl (streaming, low memory).
    Returns True on success, False on failure.
    """
    try:
        subprocess.run(
            ["curl", "-sL", "--retry", "3", "--retry-delay", "2",
             "-o", dest_path, url],
            check=True, timeout=120,
        )
        return os.path.getsize(dest_path) > 0
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError) as exc:
        print(f"  [WARN] curl failed for {url}: {exc}", file=sys.stderr)
        return False


def download_file_urllib(url, dest_path):
    """
    Fallback: download *url* to *dest_path* using urllib (streaming).
    """
    headers = {"User-Agent": "Mozilla/5.0 (compatible; ClashRuleConverter/1.0)"}
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=60) as resp:
            with open(dest_path, "wb") as fh:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    fh.write(chunk)
        return os.path.getsize(dest_path) > 0
    except (URLError, OSError) as exc:
        print(f"  [WARN] urllib failed for {url}: {exc}", file=sys.stderr)
        return False


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_conf_rules_from_file(file_path):
    """
    Parse a Shadowrocket ``.conf`` file (line by line, low memory) and
    yield ``(rule_type, value, policy)`` tuples.

    Generator — does not load the entire file into memory.
    """
    in_rule_section = False

    with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue

            # Track INI-style sections
            if line.startswith("[") and line.endswith("]"):
                in_rule_section = line.lower() == "[rule]"
                continue

            if not in_rule_section:
                continue

            # Skip comments
            if line.startswith("#"):
                continue

            # FINAL is handled by Clash's MATCH rule, not rule sets
            if line.upper().startswith("FINAL"):
                continue

            # Parse: TYPE,VALUE,POLICY[,extra...]
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 3:
                continue

            rule_type = parts[0].upper()
            value = parts[1]
            policy = parts[2].upper()

            # Filter unsupported types
            if rule_type not in DOMAIN_TYPES | KEYWORD_TYPES | IP_TYPES:
                continue
            if not value:
                continue

            yield (rule_type, value, policy)


def parse_conf_rules(content):
    """
    Parse a Shadowrocket ``.conf`` file from a string and extract rules
    from the ``[Rule]`` section.

    Returns a list of ``(rule_type, value, policy)`` tuples.
    """
    rules = []
    in_rule_section = False

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue

        # Track INI-style sections
        if line.startswith("[") and line.endswith("]"):
            in_rule_section = line.lower() == "[rule]"
            continue

        if not in_rule_section:
            continue

        # Skip comments
        if line.startswith("#"):
            continue

        # FINAL is handled by Clash's MATCH rule, not rule sets
        if line.upper().startswith("FINAL"):
            continue

        # Parse: TYPE,VALUE,POLICY[,extra...]
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue

        rule_type = parts[0].upper()
        value = parts[1]
        policy = parts[2].upper()

        # Filter unsupported types
        if rule_type not in DOMAIN_TYPES | KEYWORD_TYPES | IP_TYPES:
            continue
        if not value:
            continue

        rules.append((rule_type, value, policy))

    return rules


# ---------------------------------------------------------------------------
# Categorisation
# ---------------------------------------------------------------------------

def _policy_category(policy):
    """Map a Shadowrocket policy string to 'reject' / 'proxy' / 'direct' / None."""
    pol_lower = policy.lower()
    for p in REJECT_POLICIES:
        if p in pol_lower:
            return "reject"
    for p in PROXY_POLICIES:
        if p in pol_lower:
            return "proxy"
    for p in DIRECT_POLICIES:
        if p in pol_lower:
            return "direct"
    return None


def categorize_rules(rules):
    """
    Split rules into Clash Premium rule-set buckets.

    Returns a dict whose keys identify the output file and whose values
    are *sets* of strings ready to be written.

    Keys:
        reject_domain    – domain behavior  (ad-block domains)
        reject_ipcidr    – ipcidr behavior  (ad-block IP ranges)
        proxy_classical  – classical behavior (proxy DOMAIN-SUFFIX + DOMAIN-KEYWORD)
        proxy_ipcidr     – ipcidr behavior  (proxy IP ranges)
        direct_domain    – domain behavior  (direct domains)
        direct_classical – classical behavior (direct DOMAIN-KEYWORD, if any)
        direct_ipcidr    – ipcidr behavior  (direct IP ranges)
    """
    buckets = {
        "reject_domain": set(),
        "reject_ipcidr": set(),
        "reject_classical": set(),
        "proxy_classical": set(),
        "proxy_ipcidr": set(),
        "direct_domain": set(),
        "direct_classical": set(),
        "direct_ipcidr": set(),
    }
    for rule in rules:
        _categorise_one(buckets, rule)
    return buckets


def _categorise_one(buckets, rule):
    """Categorise a single (rule_type, value, policy) tuple into *buckets*."""
    rule_type, value, policy = rule
    cat = _policy_category(policy)
    if cat is None:
        return

    if rule_type in DOMAIN_TYPES:
        if cat == "reject":
            buckets["reject_domain"].add(value)
        elif cat == "proxy":
            buckets["proxy_classical"].add(f"{rule_type},{value}")
        elif cat == "direct":
            buckets["direct_domain"].add(value)

    elif rule_type in KEYWORD_TYPES:
        if cat == "proxy":
            buckets["proxy_classical"].add(f"DOMAIN-KEYWORD,{value}")
        elif cat == "direct":
            buckets["direct_classical"].add(f"DOMAIN-KEYWORD,{value}")
        elif cat == "reject":
            buckets["reject_classical"].add(f"DOMAIN-KEYWORD,{value}")

    elif rule_type in IP_TYPES:
        if cat == "reject":
            buckets["reject_ipcidr"].add(value)
        elif cat == "proxy":
            buckets["proxy_ipcidr"].add(value)
        elif cat == "direct":
            buckets["direct_ipcidr"].add(value)


# ---------------------------------------------------------------------------
# Output generation
# ---------------------------------------------------------------------------

def generate_txt(entries):
    """Generate a .txt rule-set file (one entry per line, sorted)."""
    return "\n".join(sorted(entries)) + "\n"


def generate_yaml(entries):
    """Generate a .yaml rule-set file with a ``payload:`` list."""
    lines = ["payload:"]
    for entry in sorted(entries):
        lines.append(f"  - {entry}")
    return "\n".join(lines) + "\n"


def write_rule_set(output_dir, name, entries):
    """Write both .txt and .yaml for *name*."""
    # .txt
    txt_path = os.path.join(output_dir, f"{name}.txt")
    with open(txt_path, "w", encoding="utf-8") as fh:
        fh.write(generate_txt(entries))
    print(f"  ✓ {name}.txt  ({len(entries):>6} entries)")

    # .yaml
    yaml_path = os.path.join(output_dir, f"{name}.yaml")
    with open(yaml_path, "w", encoding="utf-8") as fh:
        fh.write(generate_yaml(entries))
    print(f"  ✓ {name}.yaml ({len(entries):>6} entries)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Convert Shadowrocket rules to Clash Premium rule sets"
    )
    parser.add_argument(
        "--output-dir",
        default=os.path.join(os.path.dirname(__file__), "..", "rules"),
        help="Output directory for generated rule sets (default: ../rules)",
    )
    parser.add_argument(
        "--local-dir",
        default=None,
        help="Local directory containing source .conf files (skip download)",
    )
    parser.add_argument(
        "--cache-dir",
        default="/tmp/sr-cache",
        help="Directory to cache downloaded files (default: /tmp/sr-cache)",
    )
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 64)
    print(" Shadowrocket → Clash Premium Rule Sets Converter")
    print("=" * 64)

    # --- Initialise buckets ------------------------------------------------
    buckets = {
        "reject_domain": set(),
        "reject_ipcidr": set(),
        "reject_classical": set(),
        "proxy_classical": set(),
        "proxy_ipcidr": set(),
        "direct_domain": set(),
        "direct_classical": set(),
        "direct_ipcidr": set(),
    }
    total_rules = 0

    # --- Process each source file ------------------------------------------
    for filename, purpose in SR_FILES.items():
        file_path = None

        # Try local directory first
        if args.local_dir:
            local_path = os.path.join(args.local_dir, filename)
            if os.path.isfile(local_path):
                file_path = local_path
                print(f"\n[{purpose}] Using local file {filename}")

        # Otherwise download
        if file_path is None:
            url = f"{SR_BASE_URL}/{filename}"
            print(f"\n[{purpose}] Downloading {filename} ...")
            os.makedirs(args.cache_dir, exist_ok=True)
            file_path = os.path.join(args.cache_dir, filename)

            # Try curl first, fall back to urllib
            if not download_file(url, file_path):
                if not download_file_urllib(url, file_path):
                    print(f"  [WARN] Skipped {filename}")
                    continue

        # Parse and categorise on the fly (low memory)
        file_rules = 0
        for rule in parse_conf_rules_from_file(file_path):
            _categorise_one(buckets, rule)
            file_rules += 1
        total_rules += file_rules
        print(f"  Parsed {file_rules} rules")

    if total_rules == 0:
        print("\n[ERROR] No rules parsed from any source!", file=sys.stderr)
        sys.exit(1)

    # --- Generate files ----------------------------------------------------
    print(f"\nGenerating rule sets → {output_dir}/")

    file_map = {
        "reject_domain": "adblock-domain",
        "reject_ipcidr": "adblock-ipcidr",
        "reject_classical": "adblock-keyword",
        "proxy_classical": "proxy",
        "proxy_ipcidr": "proxy-ipcidr",
        "direct_domain": "direct-domain",
        "direct_classical": "direct-keyword",
        "direct_ipcidr": "direct-ipcidr",
    }

    for bucket_key, file_name in file_map.items():
        entries = buckets.get(bucket_key)
        if entries:
            write_rule_set(output_dir, file_name, entries)

    # --- Timestamp ---------------------------------------------------------
    tz_cst = timezone(timedelta(hours=8))
    now_str = datetime.now(tz_cst).strftime("%Y-%m-%d %H:%M:%S CST")
    ts_path = os.path.join(output_dir, "timestamp.txt")
    with open(ts_path, "w", encoding="utf-8") as fh:
        fh.write(f"Rule sets last updated: {now_str}\n")
        fh.write(f"Source: {SR_BASE_URL}\n")
        fh.write(f"Total raw rules parsed: {total_rules}\n")
    print(f"\n  ✓ timestamp.txt ({now_str})")

    # --- Summary -----------------------------------------------------------
    print("\n" + "-" * 64)
    print("Summary:")
    for bucket_key, file_name in file_map.items():
        count = len(buckets.get(bucket_key, set()))
        if count:
            print(f"  {file_name:<22} {count:>6} entries")
    print("-" * 64)


if __name__ == "__main__":
    main()
