# fluentbit: Fluent Bit

## Overview

Fluent Bit is a super-fast, lightweight, and highly scalable logging and metrics
processor and forwarder. Written entirely in C, it boasts an incredibly small
memory footprint (often around a few megabytes), making it the preferred sidecar
or edge agent for Kubernetes clusters and embedded Linux devices.

Unlike full-stack storage solutions, Fluent Bit is fundamentally a router and
processor. It captures logs from the host, applies regular expressions to parse
multiline strings (like Python stack traces), and routes them to dozens of
different backends simultaneously, serving as the ultimate universal translator
for system telemetry.

For OpenClaw, Fluent Bit is a phenomenal upgrade over standard Promtail or
Filebeat if you need to route logs to multiple destinations at once. If you want
to send standard Docker logs to a local VictoriaLogs instance for debugging, but
route specific LiteLLM token-usage logs to a cloud-based billing dashboard,
Fluent Bit handles that complex routing matrix with zero noticeable impact on
the host's CPU.
