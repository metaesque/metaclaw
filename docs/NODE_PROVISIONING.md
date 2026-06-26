# Bare-Metal Node Provisioning: First Principles

When unboxing dedicated hardware (Tier 1, Tier 2, or beyond) for the MetaClaw ecosystem, you must configure the machines as "Headless Servers." You will need physical access (a monitor, keyboard, and mouse) for roughly 15 minutes. After this, the HDMI cable can be unplugged forever, and the machine will sit silently in a closet or on a shelf.

## Step 1: The OS Eradication (Linux Foundation)

Consumer Mini-PCs (like GMKtec, Beelink, or Minisforum) usually ship with Windows 11 Pro. Windows introduces unacceptable overhead, forced restarts, and severe limitations regarding Docker networking and GPU PCIe pass-through.

1.  **Create Installation Media:** On your local laptop (e.g., MacBook Air), download the **Ubuntu 24.04 LTS Server** ISO (Server is preferred over Desktop to avoid UI bloat, but Desktop works if you prefer a fallback UI). Flash it to a USB drive using a tool like BalenaEtcher or Rufus.
2.  **Boot the Node:** Plug the USB, a keyboard, and an HDMI monitor into the new PC. Turn it on and repeatedly tap `F7`, `F11`, or `Delete` (depending on the BIOS) to enter the Boot Menu. Select the USB drive.
3.  **Install Ubuntu:**
    * Wipe the entire disk (destroying the Windows partition).
    * Create a standard user account (e.g., `metaclaw`).
    * **CRITICAL:** When prompted during the installation wizard, explicitly check the box to **"Install OpenSSH server."** This is the lifeline that will allow remote access.
4.  **Reboot:** Remove the USB drive when prompted and boot into the fresh Linux environment.

## Step 2: Establishing the Lifeline (Tailscale)

Currently, the node only has a local LAN IP (e.g., `192.168.1.50`). To safely access this machine from anywhere in the world without opening dangerous port-forwards on the local router, you must install the Tailscale mesh network.

1.  Log into the machine using the keyboard and monitor.
2.  Install Tailscale using their single-line curl script:
    ```bash
    curl -fsSL [https://tailscale.com/install.sh](https://tailscale.com/install.sh) | sh
    ```
3.  Authenticate the node to your tailnet:
    ```bash
    sudo tailscale up --ssh
    ```
    *(Note: The `--ssh` flag allows you to bypass managing complex SSH keys by using Tailscale's built-in cryptographic identity management).*
4.  The terminal will output an authentication URL. Type that URL into your MacBook Air or phone browser to approve the machine on your network.
5.  Run `tailscale ip -4` to print the machine's permanent, secure mesh IP (e.g., `100.x.y.z`). Write this down.

## Step 3: Severing the Physical Tether

You are now done with the physical hardware.

1.  Unplug the HDMI cable, keyboard, and mouse from the node.
2.  Leave only the Power cable and Ethernet cable (if hardwiring) connected.
3.  On your MacBook Air (which must also have Tailscale installed and authenticated), open your Terminal and connect:
    ```bash
    ssh metaclaw@100.x.y.z
    ```
4.  You are now securely connected to the node's terminal. From here, you can install Git, clone the MetaClaw repository, and run `make setup` entirely remotely.

## A Note on GUI Applications (X11 vs. Headless)

Unix supports X11 forwarding (`ssh -X`), which technically allows you to run graphical applications (like VLC or Chrome) on the remote node and have the windows appear on your MacBook Air using XQuartz.

**Do not do this.** X11 over a Wide Area Network (WAN) is unusably laggy for hardware-accelerated applications like browsers.

* **For the OpenClaw GUI:** OpenClaw runs a web server. Simply open your MacBook's native Safari or Chrome and navigate to the node's Tailscale IP: `http://100.x.y.z:18789`.
* **For Editing Code:** Do not forward GUI text editors. Use **VS Code** on your MacBook with the **"Remote - SSH"** extension. It connects to the node seamlessly, giving you a native Mac GUI while executing all file saves and terminal commands directly on the remote Linux box.
