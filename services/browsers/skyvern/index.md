# skyvern: Skyvern

## Overview

Traditional automation tools read the hidden HTML code of a website to find
buttons, which completely fails on modern, highly-secured websites that
intentionally scramble their code to block bots. Skyvern bypasses the code
entirely. It takes a screenshot of the page, passes it to a Vision LLM, and
calculates the exact pixel coordinates to click based on visual appearance.

Integrating Skyvern grants OpenClaw the ultimate anti-fragility. If a website
completely overhauls its design, renames all its code, but keeps the 'Submit'
button visually looking like a button, Skyvern will still succeed.

This capability is computationally heavy, making it ideal for OpenClaw clusters
with dedicated hardware, enabling the agent to autonomously purchase items, fill
out complex government forms, and navigate highly obfuscated enterprise portals.
