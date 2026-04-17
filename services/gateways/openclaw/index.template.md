# OpenClaw Gateway Service Setup

## Analysis Guide
The OpenClaw gateway provider does not run a complex pre-verification script
like the databases. You should simply verify that the container state is listed
as **running**.

## Terminal Onboarding
Your terminal is currently running the interactive OpenClaw Wizard. You must
navigate the text-based user interface (TUI) to initialize the cryptographic
settings.

### Navigation Rules
* Use **Up Arrow** and **Down Arrow** to navigate vertical lists.
* Use **Left Arrow** and **Right Arrow** to toggle Yes/No options.
* Press **Enter** to confirm a selection.

### The Exact Sequence
Please return to your terminal window and follow these steps:

1. **Agent "main" already exists? (Only if re-running)**
   * *Action:* Press **Left Arrow** to select **Yes**, then press **Enter**
2. **Workspace directory:**
   * *Action:* Press **Enter** to accept the default path
3. **Configure model/auth for this agent now?**
   * *Action:* Press **Left Arrow** to select **Yes**, then press **Enter**
4. **Model/auth provider:**
   * *Action:* Press **Down Arrow** exactly 10 times to highlight **LiteLLM**, then press **Enter**
5. **Enter Proxy API Key:**
   * *Action:* Copy the key below, paste it into the terminal, and press **Enter**
   * *Key:* `__MASTER_KEY__`
   * *Note:* There will be a ~20 second delay here while the app checks networking. This is normal. Wait for it to finish.
6. **Configure chat channels now?**
   * *Action:* Press **Right Arrow** to select **No**, then press **Enter**

## Graphical User Interface (GUI) Internals
The graphical control UI is accessed via the `make gui` and `make gui-setup`
targets. These targets automate a complex background authentication process.
Below is an explanation of the commands used under the hood to manage this flow.

### Accessing the OpenClaw Dashboard
Executing the command:

```bash
docker exec openclaw-gateway openclaw dashboard
```

will output something like the following:

```text
Dashboard URL: [http://127.0.0.1:18789/#token=80954a8fe](http://127.0.0.1:18789/#token=80954a8fe)...
Copy to clipboard unavailable.
No GUI detected. Open from your computer:
ssh -N -L 18789:127.0.0.1:18789 user@<host>
Then open:
http://localhost:18789/
```

The tokenized dashboard URL is the secret to accessing the dashboard.
However, there are network-binding complexities introduced by running inside a
Docker container that are automatically mitigated by our `make gui` target.

### Listing Devices
To view the current authorization state of the gateway, execute:

```bash
docker exec -e COLUMNS=200 openclaw-gateway openclaw devices list
```

This command prints out two tables: one showing all **Pending** requests, and
another showing all **Paired** devices. Passing `COLUMNS=200` expands the
internal container terminal width to 120 characters, which conveniently prevents
the 'Request' column in the Pending table from wrapping. This is highly useful
if you need to manually copy a Request ID.

**How are Pending Requests Created?** When you open the UI in your browser
without a valid token (or if your previous token was revoked), the browser's
background code immediately attempts to open a WebSocket connection. The
OpenClaw server intercepts this unauthorized connection attempt, blocks it, and
logs it in the database as a "Pending" request. The browser then displays an
informational "pairing required" message.

### Pairing A Pending Device
Once you identify a pending `<requestId>` using the list command above, you can
authorize it by executing:

```bash
docker exec -it openclaw-gateway openclaw devices approve <requestId>
```

Obtaining the device list after this will show the device has moved from the
Pending table to the Paired table.
*Note: Invoking `make gui` before pairing a device will take the user to a
dead-end login page. Invoking `make gui` after pairing will take the user
directly into the fully featured OpenClaw control dashboard.*

### Removing A Paired Device
In the 'Paired' table, the first column is 'Device', representing a `<deviceId>`.
To unpair or revoke access for a device, execute:

```bash
docker exec openclaw-gateway openclaw devices remove <deviceId>
```

**The Reconnection Loop:** Surprisingly, removing a paired device usually
results in a *new* Pending request appearing immediately. This happens because
the browser UI is constantly trying to maintain an open connection to the
server. The moment you revoke the authorization on the server side, the browser
socket drops, the browser attempts to reconnect, and the server registers that
new connection attempt as an unauthorized, pending request. After removing a
device, executing `make gui` will take you back to the login page until you
identify the new `<requestId>` and approve it.

## Next Steps
Once the interactive TUI wizard exits, return to your main terminal window.
The system will automatically patch the network routing and launch your terminal
chat interface.
