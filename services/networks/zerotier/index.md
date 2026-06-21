# zerotier: ZeroTier

## Overview

ZeroTier is an advanced Software-Defined Wide Area Network (SD-WAN) platform
that creates secure, programmable network overlays. It effectively functions as
a smart virtual Ethernet switch for the internet, operating at both Layer 2
(Data Link) and Layer 3 (Network) of the OSI model. By combining the
capabilities of VPNs and SD-WANs, it allows devices anywhere in the world to
connect as if they were physically on the same local network, using
cryptographic identities for authentication.

Within the context of a distributed MetaClaw cluster, ZeroTier offers a robust,
highly flexible alternative to Tailscale. It excels at joining disparate
physical machines—such as a GPU compute node in a datacenter and a Raspberry Pi
control plane in a home closet—into a single, unified subnet. All traffic
between nodes is end-to-end encrypted and routed peer-to-peer whenever possible,
minimizing latency for critical inter-service communication like vector database
queries.

While it requires slightly more manual configuration than Tailscale
(particularly regarding routing tables and network bridging), ZeroTier is
heavily favored by users who prefer a more open-source-centric control plane and
need complex Layer 2 bridging. However, because it lacks an out-of-the-box
feature equivalent to Tailscale Funnel for exposing local ports to the public
web, relying exclusively on ZeroTier makes receiving external webhooks from
platforms like Google Chat more difficult without additional reverse proxy
infrastructure.
