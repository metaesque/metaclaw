# Overlay Network Overview

## Providers

### Cloudflare Tunnels
Moderate Utility. This is an enterprise-grade solution for exposing internal
services to the public internet via a standard URL. It is phenomenal for webhook
ingress and provides industry-leading DDoS protection. However, it is not a true
mesh VPN. It cannot be used to easily SSH between your cluster nodes or securely
hide your OpenClaw dashboard behind a private, un-routable IP space.
Furthermore, Cloudflare terminates TLS at their edge, meaning they technically
have access to your decrypted webhook traffic.

### Tailscale
Highest Utility. Tailscale is the optimal default for OpenClaw. It seamlessly
handles both full-mesh cluster routing (giving every node a static `100.x.y.z`
IP for internal communication) and public webhook ingress (via Tailscale
Funnel). It requires almost zero configuration and provides end-to-end encrypted
remote access to the OpenClaw dashboard and SSH terminals.

### ZeroTier
High Utility. ZeroTier is a highly performant, open-source-friendly alternative
to Tailscale for building the internal cluster mesh. It operates at Layer 2/3
and is exceptional for linking multi-cloud or hybrid environments. However, it
ranks below Tailscale because it lacks an integrated "Funnel" equivalent, making
it difficult to receive external webhooks (like Telegram messages) without
setting up a separate public VPS to bridge the traffic.
