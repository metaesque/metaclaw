# loki: Grafana Loki

## Overview

Grafana Loki is a highly scalable, multi-tenant log aggregation system heavily
inspired by Prometheus. Instead of indexing the full text of every single log
line, it indexes only the metadata (labels), compressing the raw log data into
discrete chunks. Promtail acts as the dedicated agent, tailing log files,
attaching the relevant labels, and forwarding them directly to Loki.

This metadata-only indexing approach makes Loki incredibly lightweight and cost-
effective compared to traditional full-text search engines. It excels in
environments where users are already utilizing Grafana and Prometheus, allowing
them to seamlessly correlate system metrics with application logs using the same
label-driven querying language (LogQL).

For OpenClaw, Loki remains a phenomenal standard default. OpenClaw agents run on
hardware where preserving RAM and SSD I/O is critical. By indexing only labels
(like `container_name=openclaw-gateway`), Loki allows developers to monitor
agent thought processes and tool-execution errors securely without the massive
memory overhead required to index every generated word of an LLM's output.
