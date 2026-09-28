# tor-exit-nodes

Up-to-date list of running Tor relays, fetched hourly from [Onionoo](https://onionoo.torproject.org/) (`type:relay running:true`).

## Generated files

| File | Contents |
|---|---|
| `tor_relays.csv` | One relay per row with `fingerprint, or_addresses, exit_addresses, country, country_name, as, as_name` |
| `tor_relays_ips.txt` | All deduplicated IPs (IPv4 + IPv6), one per line |
| `tor_relays_ips_ipv4.txt` | IPv4 IPs only, one per line |
| `tor_relays_ips_ipv6.txt` | IPv6 IPs only, one per line |

Raw links: [CSV](tor_relays.csv) · [IPs](tor_relays_ips.txt) · [IPv4](tor_relays_ips_ipv4.txt) · [IPv6](tor_relays_ips_ipv6.txt)