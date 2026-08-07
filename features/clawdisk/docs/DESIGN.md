# ClawDisk

**ClawDisk** is the official distributed storage mesh feature of MetaClaw.

## Scope and Purpose

The primary objective of ClawDisk is to unify isolated storage mediums across the cluster into a single, seamless, high-performance virtual filesystem. It ensures that all Internal NVMe SSDs and external nomadic SSDs physically attached to any host on the LAN are automatically mounted, exported, and accessible by every other host on the LAN.

## Canonical Naming Schema

ClawDisk enforces strict, deterministic namespace parity to ensure scripts and agents can reliably locate data regardless of which physical node they are executing on:

1.  **Remote Home Directories:**
    On any `<host1>`, accessing `/mnt/cluster/<host2>/home/metaclaw` guarantees read-write access to `<host2>`'s local `/home/metaclaw` directory. This is tightly scoped to prevent accidental access to `<host2>`'s root (`/`) OS filesystem.
2.  **Nomadic External SSDs:**
    On any `<host1>`, accessing `/mnt/cluster/ext/<name>` guarantees read-write access to the external SSD identified by `<name>` (e.g., `t9_2tb_black`). The path remains identical and valid regardless of which physical host the drive is currently plugged into.

## Hardware Optimization & Network Topology

ClawDisk is designed to automatically utilize the fastest available physical layer for data transfer.

While the cluster defaults to the Tailscale mesh overlay (`100.x.x.x`) for universal connectivity, ClawDisk actively searches for optimized hardware routes. For example, `spark1` and `spark2` are connected via a TRANSUTON 200G QSFP56 PAM4 Direct Attach Copper (DAC) Twinax Cable.

If ClawDisk detects matching DAC IPs in the hardware registry for both the source and target node, it bypasses the Tailscale encryption overhead and explicitly maps the AutoFS/NFS routes over the raw 200GbE physical link.

## Implementation Architecture

ClawDisk is not an isolated microservice. It relies heavily on the shared abstractions provided by the MetaClaw platform:
*   **Hardware Registry:** Uses the global `lib/devices.py` abstract classes to discover UUIDs, bus connections, and dynamic nomadic node tracking (`current_host`).
*   **Execution:** Setup routines (e.g., `clawdisk_setup.py`) leverage standard OS packages (`autofs`, `nfs-kernel-server`, `exfat` FUSE mapping) to manipulate the Linux Virtual Filesystem (VFS).
