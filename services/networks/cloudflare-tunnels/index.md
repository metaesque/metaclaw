# cloudflare-tunnels: Cloudflare Tunnels

## Overview

Cloudflare Tunnels (powered by the `cloudflared` daemon) provides a secure way
to expose local web servers and applications to the internet without opening any
incoming ports on a router or firewall. Instead of listening for connections,
the daemon creates an outbound, encrypted connection to the Cloudflare global
network. External users hit a standard Cloudflare URL, and the traffic is routed
securely back down the tunnel to the local machine.

In the MetaClaw ecosystem, Cloudflare Tunnels are the premier solution for
public ingress, specifically for webhooks. If an OpenClaw agent integrates with
external SaaS applications (like receiving a GitHub issue creation event or a
Slack message), those services must reach the agent. The tunnel provides a
stable HTTPS endpoint that bypasses Carrier-Grade NAT (CGNAT) and residential
firewalls completely.

While highly effective for webhooks, Cloudflare Tunnels introduce a specific
security trade-off: Cloudflare terminates the TLS encryption at their edge
nodes. This means Cloudflare has the technical ability to inspect the decrypted
traffic before forwarding it to your local node. For teams requiring strict end-
to-end encryption without third-party decryption, or for establishing a full
peer-to-peer mesh between multiple cluster nodes, alternative tools like
Tailscale or ZeroTier are more appropriate.
