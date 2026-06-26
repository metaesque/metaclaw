# weaviate: Weaviate

## Overview

Weaviate is an open-source, Go-based vector database that stands out by offering
built-in machine learning modules and a flexible GraphQL API. It can
automatically vectorize text on ingestion if configured to do so, bridging the
gap between raw data storage and embedding generation.

For OpenClaw, Weaviate offers a developer-friendly query interface and rich
filtering capabilities. It allows agents to structure their memories using an
intuitive graph-like syntax, making complex semantic traversals easier to
encode.

However, since OpenClaw typically relies on LiteLLM for routing and unified
embedding generation, some of Weaviate's native vectorization features may be
redundant in this specific framework. Despite this, its robust community and
integration ecosystem make it a highly capable memory backend.
