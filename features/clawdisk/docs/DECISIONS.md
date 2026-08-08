# Feature ClawDisk: Architecture Decision Records (ADRs)

This document tracks the engineering choices and lessons learned during the development of ClawDisk, the MetaClaw distributed storage mesh.

## ADR 1: Decoupling Storage Automation from `lib/devices.py`

**Context:**
Originally, all OS-level mount logic, NFS exports, and AutoFS configuration was baked directly into the `ComputeNode.mount_storage()` method within `lib/devices.py`.

**Decision:**
The mutation logic was stripped out of the abstract object model and placed into a standalone, modular script: `features/clawdisk/bin/clawdisk_setup.py`.

**Justification:**
While object-oriented design makes it tempting to allow a node to "configure itself", embedding 150+ lines of raw bash execution (Netplan config, FUSE wrappers, NFS exports) into the central device API created a massive God-Object. It violated the core MetaClaw principle (ADR 1 in `features/DECISIONS.md`) that infrastructure capabilities should be isolated into modular features. The `devices.py` library now strictly answers "What hardware exists?", while `clawdisk_setup.py` answers "How do we mesh it together?".

## ADR 2: Bypassing NFS `exfat` Kernel Limitations via FUSE

**Context:**
Nomadic external SSDs in the MetaClaw ecosystem are primarily formatted as `exfat` to guarantee native cross-platform compatibility with macOS client laptops. However, when attempting to export these drives over the cluster LAN, `exportfs` continually rejected the mounts with the error: `does not support NFS export`.

**Decision:**
ClawDisk dynamically intercepts any drive configured as `exfat` in the hardware registry, unmounts it, and forces it to mount into userspace using the `exfat-fuse` driver.

**Justification:**
The modern, in-kernel Linux `exfat` driver physically lacks the `export_operations` data structure. Because FAT-based filesystems do not possess persistent inodes, the kernel-level NFS server refuses to generate the file handles required to share the drive. By pivoting to the older `exfat-fuse` userspace driver, we trick the NFS daemon into generating compatible file handles, allowing seamless network sharing without forcing the user to reformat their macOS-compatible drives to `ext4`.

## ADR 3: Stateless AutoFS Replicated Server Failover

**Context:**
To track nomadic SSDs as they were moved between nodes (e.g., from `spark1` to `spark2`), the original implementation relied heavily on dynamically updating a `current_host` symlink in the static JSON registry and attempting to sync that state across the cluster. This proved incredibly brittle, resulting in AutoFS deadlocks and empty ghost directories whenever state synchronization lagged behind physical reality.

**Decision:**
Stateful tracking was abandoned. AutoFS maps now utilize replicated server failover syntax. Every node in the cluster generates an identical AutoFS map for every SSD, appending a comma-separated list of all dynamic Tailscale IPs in the cluster (e.g., `100.x.1.1,100.x.1.2:/mnt/cluster/ext/drive`).

**Justification:**
By supplying a comma-separated list of all possible hosts, we shift the discovery burden natively onto the AutoFS daemon. Because nodes now *only* export an SSD via NFS if it is physically attached to their local USB ports, the AutoFS daemon will simply ping the list in order, fail-fast on the nodes that reject the connection, and instantly mount the drive from whichever node actually has it. This completely eliminates the need to track `current_host` state.
