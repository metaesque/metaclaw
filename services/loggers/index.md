# Log Aggregator Overview

## Providers

### Grafana Loki
The Standard Default. Excellent label-based log compression. Ideal if the user
is already running Prometheus/Grafana on their local network.

### SigNoz
The Observability Suite. Unmatched for Phase 4 roadmap goals. Correlating traces
to logs is essential for debugging multi-agent orchestration loops.

### Graylog
The Security Backstop. Valuable only if the agent is given root access and
requires immediate, automated kill-switches via SIEM alerting.

### OpenSearch
The Enterprise Standard. Provides massive analytical depth but requires
dedicated infrastructure. An open-source alternative to ELK.

### Quickwit
The Context Lake Engine. Best for dumping petabytes of long-term agent telemetry
to cheap S3/external storage while maintaining sub-second search.

### ELK Stack
Architectural Overkill. While powerful, the JVM RAM requirements will instantly
starve local LLM runners of necessary resources on edge hardware.

### Fluent Bit
The Universal Router. The best lightweight sidecar for routing logs to multiple
destinations without acting as a storage backend itself.

### VictoriaLogs
The Ultimate Edge Database. Replaces Loki as the top choice due to its ability
to perform full-text search while consuming 30x less RAM. Practically invisible
to the host OS.

### Vector
The Privacy Sanitizer. The VRL language makes it the top choice for
mathematically ensuring PII is stripped from agent logs before storage.
