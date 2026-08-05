# Feature Kasa: Agent Directives & Constraints

This document extracts the strict technical requirements from `DESIGN.md`.
Developer agents must adhere to these rules when implementing the Kasa
telemetry system.

## Required CLI Interface

*   `daemon`: Continuous polling loop.
*   `poll`: Single network discovery and telemetry log.
*   `move`: Map a device UID to a physical strip MAC and plug index.
*   `rename`: Update a device UID or human-readable name.
*   `query`: Retrieve historical data by date range.
*   `price`: Update cost per kWh.
*   `backup`: Snapshot the database.
*   `state`: Print database schema state.

## Integration Rules

*   Output format must be compatible with Telegraf's `inputs.exec` plugin
    (JSON or Influx Line Protocol).
*   Must support future extensibility for thermal and VRAM metrics.

## Data Rules

*   Must use local durable state (SQLite) tracking Slowly Changing Dimensions
    (SCD Type 2) for device mappings.

## Testing Rules

*   Unit tests are strictly required.
*   Must follow the 1:1 `bin/` to `tests/` directory mapping rule as defined
    in the meta-level `projects/AGENTS.md`.

