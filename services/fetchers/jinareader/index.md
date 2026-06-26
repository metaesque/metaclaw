# jinareader: Jina AI Reader

## Overview

Jina Reader requires absolutely no complex SDKs, local dependencies, or heavy
browser installations. By simply prepending `https://r.jina.ai/` to a URL, the
service's cloud infrastructure uses headless browsers to render the page,
execute JavaScript, and apply readability algorithms to strip away ads and
navigation menus.

For OpenClaw, this is the lowest-friction fetcher available. It is a drop-in
replacement for the default fetching logic. The agent simply modifies the URL
string it requests, and it receives perfectly clean text in return.

Because the processing happens entirely on Jina's servers, it is the ultimate
solution for OpenClaw nodes running on severely constrained hardware (like a
Raspberry Pi or an older MacBook) where running a local Chromium instance would
cause the system to crash.
