# Feature Kasa: Technical Implementation

## Stateless Architecture

The feature has completely transitioned away from maintaining local SQLite
database state. It now functions as a stateless, single-execution python
script designed to be consumed by the Telegraf daemon via the `inputs.exec`
plugin.

## Script Execution (`power_kasa.py`)

The `power_kasa.py` script no longer utilizes a complex `argparse` CLI. Upon
execution, it performs the following linear steps:

1.  Reads the static device mappings from `data/hardware.json`.
2.  Utilizes the `psutil` library to extract current Host CPU %, Memory %,
    and CPU core temperatures.
3.  Utilizes the `python-kasa` library to broadcast a UDP discovery packet
    across the local LAN, finding all active HS300 power strips.
4.  Queries the internal energy modules of the discovered strips to acquire
    real-time wattage, voltage, and amperage per plug.
5.  Outputs the combined Host and Kasa metrics to `stdout` strictly formatted
    in **Influx Line Protocol**.

## Observability Definitions

*   **Grafana Dashboard:** The visual representation of the metrics is defined
    as a V2 JSON model in `assets/visualizers/grafana/dashboards/kasa/dashboard.json`. It provides immediate
    time-series graphs for power draw (Watts) per device and Host CPU
    temperatures.
*   **VictoriaMetrics Alerts:** Anomaly detection thresholds (e.g., Circuit
    loads exceeding 1500W, CPU thermals exceeding 85°C) are defined using
    PromQL inside `data/alerts.yaml` for ingestion by the `vmalert` daemon.

## Testing Architecture

The feature maintains `test_power_kasa.py` which strictly enforces test
coverage for the refactored stateless functions. Standard `unittest.mock`
patching is heavily utilized to isolate the `psutil` hardware queries and
the asynchronous `kasa.Discover` network calls.

