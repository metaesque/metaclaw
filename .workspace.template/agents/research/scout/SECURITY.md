# SECURITY.md - Scout Constraints
- **Rate Limiting:** Never hit the same domain more than 3 times in a single execution loop to avoid triggering WAF (Web Application Firewall) bans.
- **Paywalls:** If a target URL requires authentication or throws a 403 Forbidden / CAPTCHA challenge, immediately abort the fetch and report the barrier. Do not attempt to confabulate the missing data.

