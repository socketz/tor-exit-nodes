# tor-exit-nodes

**An up-to-date list of Tor exit nodes, automatically generated every hour from the Onionoo API.**

[![Sync](https://github.com/socketz/tor-exit-nodes/actions/workflows/sync.yml/badge.svg)](https://github.com/socketz/tor-exit-nodes/actions/workflows/sync.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📌 What is this?

This repository keeps a **local, always-fresh copy** of Tor relays that are currently running and acting as exit nodes. The data is pulled from the Tor Project's [Onionoo API](https://metrics.torproject.org/onionoo.html) using the query `type:relay running:true`, and it is regenerated **every hour** via GitHub Actions.

It is useful for:

- **Security researchers** who need to identify traffic coming from the Tor network.
- **Developers** building fraud detection, log analysis, or threat intelligence tools.
- **Anyone** who needs a reliable list of Tor exit IPs without depending on third-party services.

## 📂 Generated files

| File | Contents |
|---|---|
| [`tor_relays.csv`](tor_relays.csv) | One relay per row with: `fingerprint, or_addresses, exit_addresses, country, country_name, as, as_name` |
| [`tor_relays_ips.txt`](tor_relays_ips.txt) | All deduplicated IPs (IPv4 + IPv6), one per line |
| [`tor_relays_ips_ipv4.txt`](tor_relays_ips_ipv4.txt) | IPv4 addresses only, one per line |
| [`tor_relays_ips_ipv6.txt`](tor_relays_ips_ipv6.txt) | IPv6 addresses only, one per line |

> 💡 **Direct raw links:** You can also download the files from the [Releases](https://github.com/socketz/tor-exit-nodes/releases) section under the `data` tag.

## ⚙️ How it works

1. **GitHub Actions** triggers the `sync.yml` workflow every hour (`cron: '0 * * * *'`). It can also be run manually from the *Actions* tab.
2. The script [`src/onionoo_fetch.py`](src/onionoo_fetch.py) queries the Onionoo API, paginating results in blocks of 500 relays with 16 parallel workers.
3. The data is validated (minimum 1000 relays to avoid publishing partial snapshots) and consolidated into the four output files.
4. If the data has changed, an automatic commit is made and the release tagged `data` is updated.

**Fault tolerance:**

- Up to 3 retries with exponential backoff per request.
- If reconciliation shows more than 100 missing relays compared to the expected total, the process aborts to avoid publishing incomplete data.

## 🚀 Quick start

### Get all IPs (IPv4 + IPv6)

```bash
curl -s https://raw.githubusercontent.com/socketz/tor-exit-nodes/master/tor_relays_ips.txt
```

### Get IPv4 only

```bash
curl -s https://raw.githubusercontent.com/socketz/tor-exit-nodes/master/tor_relays_ips_ipv4.txt
```

### Get the full CSV

```bash
curl -s -O https://raw.githubusercontent.com/socketz/tor-exit-nodes/master/tor_relays.csv
```

### Python example

```python
import pandas as pd

url = "https://raw.githubusercontent.com/socketz/tor-exit-nodes/master/tor_relays.csv"
df = pd.read_csv(url)
print(df[["fingerprint", "country", "as_name"]].head())
```

## 🛠️ Local development

If you want to run the pipeline on your own machine:

```bash
# Clone the repository
git clone https://github.com/socketz/tor-exit-nodes.git
cd tor-exit-nodes

# Run the script (no external dependencies, just Python 3)
python3 src/onionoo_fetch.py
```

The files will be generated in the root directory. No additional libraries are required: the script uses only the Python standard library.

## 🔧 Customization

You can tweak the behavior by editing the constants at the top of `src/onionoo_fetch.py`:

| Constant | Default value | Description |
|---|---|---|
| `PAGE` | 500 | Relays per page in each request |
| `WORKERS` | 16 | Parallel threads for fetching |
| `MIN_RELAYS` | 1000 | Minimum relays required to consider a snapshot valid |
| `CHURN_TOLERANCE` | 100 | Maximum allowed difference between reconciliations |

## 📅 Update frequency

- **Automatic:** every hour, on the hour (UTC).
- **Manual:** you can trigger the workflow from the *Actions* tab → *Sync* → *Run workflow*.

## 📜 License

### Source code

The **source code** in this repository (`src/`, `.github/`) is released under
the MIT License. See the [LICENSE](LICENSE) file for details.

### Data

The **data files** (`tor_relays.csv`, `tor_relays_ips*.txt`) are generated from
the [Onionoo API](https://metrics.torproject.org/onionoo.html) provided by the
[Tor Project](https://www.torproject.org/).

- The Onionoo software is licensed under the
  [Apache License 2.0](https://gitlab.torproject.org/tpo/network-health/metrics/onionoo/-/blob/master/LICENSE).
- Tor network metrics data is made available by the Tor Project under a
  [CC0 no copyright declaration](https://creativecommons.org/publicdomain/zero/1.0/).
- This repository is **not affiliated with or endorsed by** the Tor Project.

When using or redistributing these data files, please credit the Tor Project as
the original source.

---

**⭐ If this repository is useful to you, please consider giving it a star. It helps more people find it.**
