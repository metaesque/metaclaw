# Feature Kasa: Hardware Telemetry & Power Monitoring

## Context & Objectives

This feature provides real-time monitoring of power consumption and hardware
metrics across the personal AI compute farm. Initially focused on the Kasa
HS300 power strip, the scope serves as a generalized hardware
telemetry collector natively embedded inside MetaClaw.

The primary objective is to build a robust Python application
(`power_kasa.py`) that gathers telemetry, manages slowly changing dimensions
(such as device mapping and electricity pricing), and seamlessly integrates
with the MetaClaw observability stack (VictoriaMetrics + Telegraf + Grafana).

## Functional Requirements

The application must expose a robust Command Line Interface (CLI) supporting
the following operational modes:

*   **Daemon Mode (`daemon`)**: A continuous polling loop designed to be
    managed by `systemd`.
*   **Discovery & Polling (`poll`)**: Manual trigger to discover Kasa strips
    on the LAN and log immediate telemetry.
*   **Device Management (`move`, `rename`)**: Capabilities to map logical
    devices (e.g., "Inference Node 1") to physical power strip plugs, and
    rename them as infrastructure evolves.
*   **Data Retrieval (`query`)**: Retrieve historical telemetry data filtered
    by date ranges and device identifiers.
*   **Financial Tracking (`price`)**: Update the cost per kWh threshold to
    track active electricity expenditure.
*   **Maintenance (`backup`, `state`)**: Provide safe snapshots of the
    underlying data store and output current schema states.

## Integration Constraints

The software team must ensure the application adheres to the following
external integration constraints:

*   **Telemetry Forwarding**: The application must be capable of outputting
    metrics in a format natively digestible by Telegraf (specifically
    utilizing the `inputs.exec` plugin). JSON output with clear key-value
    metrics and tags is preferred.
*   **Metric Expansion**: The architecture must be extensible. While
    currently focused on instantaneous Watts, Volts, Amps, and kWh, it must
    easily scale to ingest thermal data (CPU/GPU temps), VRAM utilization,
    and network mesh latency.

## Data Persistence Strategy

The application must maintain local, durable state. While the specific
database engine and schema design are left to the discretion of the
`software_orchestrator`, the system must conceptually track:

*   Physical Hardware (Strips and Plugs).
*   Logical Entities (Devices plugged into the hardware).
*   Temporal Mappings (SCD Type 2 tracking of which device was plugged in
    where, and at what time).
*   High-frequency metric samples.
*   Daily hardware-accumulated energy totals.

## Testing Mandates

*   Comprehensive unit testing is strictly required for all core functions,
    classes, and data transformations.
*   Test files must utilize standard Python testing frameworks (e.g.,
    `unittest` or `pytest`).
*   The exact namespace and directory structure for the test files must
    follow the 1:1 mapping standard (`bin/` to `tests/`).

