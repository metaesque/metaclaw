# quickwit: Quickwit

## Overview

Quickwit is an open-source, cloud-native search engine written in Rust,
specifically optimized for massive, append-only observability datasets like logs
and distributed traces. Its defining architectural trait is the complete
decoupling of compute and storage; it indexes data directly into highly
compressed columnar formats and stores them on cheap object storage (like AWS S3
or local equivalents), while remaining capable of executing sub-second full-text
searches.

The system achieves massive scalability by running stateless searchers and
indexers that operate directly against immutable files in object storage. This
eliminates the nightmare of shard rebalancing found in traditional search
engines and results in a 90% storage cost reduction compared to heavy Java-based
alternatives.

In an OpenClaw ecosystem, Quickwit shines as the ultimate backend for long-term
"Context Lakes" or massive audit trails. If an agent is running continuously for
months—scraping the web, generating code, and executing thousands of API calls
per day—the volume of logging data will quickly overwhelm standard local SSDs.
Quickwit allows OpenClaw to dump terabytes of historical agent telemetry
directly onto a cheap external drive or a remote S3 bucket, while keeping that
data instantly searchable for debugging without requiring an expensive, always-
on cluster.
