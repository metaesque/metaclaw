# convex: Convex

## Overview

Convex is a reactive backend-as-a-service designed for modern full-stack
TypeScript applications. It unifies a database, serverless functions, and real-
time state synchronization via WebSockets into a single platform. When data
changes in the Convex database, those changes are immediately and reactively
pushed to connected clients without the need for polling.

For an OpenClaw agent, Convex provides a uniquely reactive memory layer. Instead
of the agent needing to constantly poll for changes or rely entirely on cron
jobs, external events (like a user updating a preference in a UI, or another
sub-agent completing a task) can be instantly pushed into the agent's active
context window. Convex also includes managed vector search functionality. This
means OpenClaw can offload the heavy lifting of embedding management and
similarity search to the Convex backend.

The agent simply subscribes to its memory stream, ensuring its context is always
perfectly synchronized with external state changes in real-time.
