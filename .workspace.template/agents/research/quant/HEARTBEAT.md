# HEARTBEAT.md - Proactive Checks

Execute this loop once every 24 hours at market close.

1. **Exchange Fee Audit:** Query the live APIs for Kraken, Coinbase, and Wealthsimple. Calculate the exact slippage and fee cost of moving $10,000 CAD into BTC and subsequently into cold storage. Flag any spread anomalies.
