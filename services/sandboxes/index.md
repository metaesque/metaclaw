# Execution Sandbox Overview

## Providers

### Docker
Unsafe for Code Execution. Perfect for packaging the OpenClaw framework itself,
but fatally flawed for agent code execution due to shared host kernel
vulnerabilities.

### gVisor
gVisor is a user-space application kernel developed by Google that provides a
strong layer of hardware-agnostic isolation for containers. By intercepting
application system calls and acting as the guest kernel, it provides boundary
defenses that standard Docker lacks, preventing malicious or hallucinated code
from compromising the host OS.

### Hardened Docker DooD
Provides a hardened, sterile execution environment for the Sandbox service. If
your OpenClaw agent hallucinates a dangerous Python or Bash script, or is
tricked via prompt injection into running malicious code, this environment
ensures the code cannot escape and compromise your host machine.

### Firecracker
The Enterprise Standard. Offers unmatched KVM hardware isolation and millisecond
boot times. However, the extreme orchestration complexity makes it unviable for
standard personal deployments.

### E2B
The Cloud-Offload Solution. The easiest way to achieve hardware-level microVM
security. Highly recommended if the user is willing to pay for cloud execution
and sacrifice offline capability.
