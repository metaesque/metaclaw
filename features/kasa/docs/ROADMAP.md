# Feature Kasa: ROADMAP

This document serves as the active working memory for the Kasa Hardware
Telemetry feature. It tracks current progress, immediate next steps, and
long-term milestones.

## Current State: Phase 1 (Complete)

The initial MVP has been achieved. The project successfully queried Kasa
HS300 power strips locally, logging high-frequency wattage/voltage data to a
local SQLite database.

## Active Phase: Phase 2 - Observability Pipeline Integration (Complete)

**Goal:** Transition the script from a standalone SQLite logger to a
stateless telemetry collector that feeds the global MetaClaw observability
stack (Telegraf + VictoriaMetrics).

*   [x] **Task 1: Telegraf Exec Format output**
    *   Refactored `power_kasa.py` to output exclusively in Influx Line
        Protocol format.
    *   Removed the entire `PowerDB` SQLite backend and legacy CLI commands.

*   [x] **Task 2: Decouple Configuration from State**
    *   Extracted the "Device to Plug" mappings into a static YAML file
        (`data/kasa_config.yaml`).
    *   The script reads this config on execution to tag the metrics
        correctly, allowing it to be entirely stateless.

*   [x] **Task 3: Expand Telemetry Scope (Host Metrics)**
    *   Integrated OS-level Python calls (`psutil`) to capture CPU
        temperatures, and Memory load.
    *   Output these new metrics in the same structured format for Telegraf.

## Active Phase: Phase 3 - Dashboarding & Alerts (Complete)

**Goal:** Visualize the gathered data and implement programmatic alert
routing.

*   [x] **Task 4: Grafana Dashboard Definition**
    *   Designed a `dashboard.json` for Grafana that queries VictoriaMetrics.
    *   Created panels for "Power Draw per Device" and "Host CPU Temperature".

*   [x] **Task 5: Anomaly Alerting**
    *   Configured VictoriaMetrics vmalert rules in `data/alerts.yaml` to
        detect threshold breaches (e.g., "CPU Temp > 85C" or "Power Draw >
        1500W").

