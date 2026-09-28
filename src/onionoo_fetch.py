#!/usr/bin/env python3
"""Fetch running Tor relays from Onionoo and generate CSV + IP lists."""

import concurrent.futures
import csv
import ipaddress
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://onionoo.torproject.org/details"
SEARCH = "type:relay running:true"
FIELDS = "fingerprint,or_addresses,exit_addresses,country,country_name,as,as_name"
PAGE = 500
WORKERS = 16
RETRIES = 3
TIMEOUT = 60
MIN_RELAYS = 1000
CHURN_TOLERANCE = 100
USER_AGENT = "tor-exit-nodes/1.0"

CSV_NAME = "tor_relays.csv"
IPS_ALL = "tor_relays_ips.txt"
IPS_V4 = "tor_relays_ips_ipv4.txt"
IPS_V6 = "tor_relays_ips_ipv6.txt"


def build_url(offset):
    params = urllib.parse.urlencode(
        {
            "search": SEARCH,
            "fields": FIELDS,
            "limit": PAGE,
            "offset": offset,
        },
        quote_via=urllib.parse.quote,
    )
    return f"{BASE_URL}?{params}"


def http_get_json(url):
    last_error = None
    for attempt in range(RETRIES):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code < 500:
                raise
        except Exception as error:
            last_error = error
        if attempt < RETRIES - 1:
            time.sleep(2 * (2 ** attempt))
    raise last_error


def fetch_page(offset):
    return http_get_json(build_url(offset))


def validate_snapshot(page):
    relays = page.get("relays")
    published = page.get("relays_published")
    if not isinstance(relays, list) or not isinstance(published, str) or not published:
        raise RuntimeError(
            "unexpected Onionoo response: missing relays or relays_published"
        )
    total = len(relays) + page.get("relays_truncated", 0)
    if total < MIN_RELAYS:
        raise RuntimeError(
            f"unexpectedly low relay count ({total} < {MIN_RELAYS}); "
            "aborting to avoid publishing empty or partial data"
        )
    return total


def merge_pages(relays, pages):
    for page in pages:
        for relay in page.get("relays", []):
            relays[relay["fingerprint"]] = relay
    return relays


def fetch_relays():
    first = fetch_page(0)
    total = validate_snapshot(first)
    published = first.get("relays_published", "")

    offsets = list(range(PAGE, total + PAGE, PAGE))
    pages = [first]
    if offsets:
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
            pages.extend(executor.map(fetch_page, offsets))
    relays = merge_pages({}, pages)

    probe = fetch_page(0)
    target = validate_snapshot(probe)
    merge_pages(relays, [probe])

    for _ in range(2):
        if len(relays) >= target:
            break
        offsets = list(range(len(relays), target + PAGE, PAGE))
        with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
            merge_pages(relays, executor.map(fetch_page, offsets))

    if len(relays) < target - CHURN_TOLERANCE:
        raise RuntimeError(
            f"incomplete snapshot: {len(relays)}/{target} relays after "
            "reconciliation; aborting to avoid publishing partial data"
        )
    if len(relays) < target:
        print(
            f"WARNING: captured {len(relays)} of {target} relays "
            f"(within tolerance {CHURN_TOLERANCE}); the relay set changed mid-fetch",
            file=sys.stderr,
        )

    return relays, published


def write_csv(relays):
    tmp = CSV_NAME + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            ["fingerprint", "or_addresses", "exit_addresses", "country",
             "country_name", "as", "as_name"]
        )
        for fingerprint in sorted(relays):
            relay = relays[fingerprint]
            writer.writerow(
                [
                    fingerprint,
                    " ".join(relay.get("or_addresses", [])),
                    " ".join(relay.get("exit_addresses", [])),
                    relay.get("country", ""),
                    relay.get("country_name", ""),
                    relay.get("as", ""),
                    relay.get("as_name", ""),
                ]
            )
    os.replace(tmp, CSV_NAME)


def strip_port(entry):
    if entry.startswith("["):
        end = entry.find("]")
        return entry[1:end] if end != -1 else entry[1:]
    return entry.rsplit(":", 1)[0]


def add_ip(text, v4, v6):
    try:
        address = ipaddress.ip_address(text.strip())
    except ValueError:
        return
    (v4 if address.version == 4 else v6).add(address)


def collect_ips(relays):
    v4, v6 = set(), set()
    for relay in relays.values():
        for entry in relay.get("or_addresses", []) + relay.get("exit_addresses", []):
            add_ip(strip_port(entry), v4, v6)
    return v4, v6


def write_ip_file(path, addresses):
    tmp = path + ".tmp"
    with open(tmp, "w", newline="\n", encoding="utf-8") as handle:
        for address in addresses:
            handle.write(str(address) + "\n")
    os.replace(tmp, path)


def main():
    relays, published = fetch_relays()
    write_csv(relays)
    v4, v6 = collect_ips(relays)
    write_ip_file(IPS_ALL, sorted(v4) + sorted(v6))
    write_ip_file(IPS_V4, sorted(v4))
    write_ip_file(IPS_V6, sorted(v6))
    print(
        f"relays_published={published} "
        f"relays={len(relays)} ips_v4={len(v4)} ips_v6={len(v6)}"
    )


if __name__ == "__main__":
    sys.exit(main())