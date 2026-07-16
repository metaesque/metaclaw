# MetaClaw Changelog

## [Unreleased]
### Added
- `bin/power_kasa.py`: Local energy telemetry script for TP-Link Kasa HS300 power strips. Features real-time JSONL data logging, delta calculations, and historical 30-day daily summary extraction.
- Support for safe headless Wi-Fi provisioning of IoT devices via `nmcli` without disrupting Tailscale mesh routing.

### Changed
- `bin/orchestrate.py`: Enhanced dynamic environment seeding for Tier 2 clusters. Automatically populates LiteLLM configurations to route `SIMPLE_MODEL`, `MEDIUM_MODEL`, and `COMPLEX_MODEL` to local Ollama instances.
- `services/proxies/litellm/config.yaml`: Updated predictive routing tiers to respect dynamically injected local endpoints.

### Fixed
- Addressed 403 API Key Leak error by restructuring environment variable fallback chains and removing hardcoded plaintext keys from default configurations.
- Suppressed `python-kasa` DeprecationWarnings for `is_strip` and `emeter_realtime` by migrating to the `DeviceType` and `Module.Energy` APIs.

## [0.1.0] - Initial Foundation
- Initial project structure, Docker Compose services, and orchestrator scripts.
- MetaClaw protocol definitions and Basekit UI component rules established.
