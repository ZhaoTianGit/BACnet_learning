# Changelog

All notable changes to the Automated BACnet Commissioning Framework will be documented in this file. 
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [v0.1.0] - Base Automation & Network Routing - 2026-02-27

### Added
- **Phase 0 Radar Sweep (Bus Enumeration):** Implemented `bacnet.whois()` global broadcast to dynamically discover the DUT and pre-cache network routing.
- **Test Vector Injection:** Automated the writing process to `Present_Value` to simulate boundary setpoints (e.g., 31.0 °C).
- **Hardware Decoupling (Force Override):** Implemented BACnet `Out_of_Service = True` override prior to injection, safely bypassing the controller's internal logic loops.
- **Terminal UI Enhancements:** Integrated the `rich` library for high-contrast, color-coded execution logs and beautiful traceback interception.

### Changed
- **Async Architecture:** Migrated the entire execution flow to Python's `asyncio` to support non-blocking network I/O for future high-concurrency polling.
- **Standardized Terminology:** Updated all inline documentation and console outputs to strictly use hardware validation terminology (DUT, Testbench, Test Vector).
- **Network Routing:** Refined target mapping to explicitly use point-to-point IP and the standard BACnet port (`192.168.100.183:47808`) for clean-room testing environments.

### Fixed
- **Windows Socket Compatibility (Monkey Patch):** Applied a top-level dynamic override to `asyncio.base_events._set_reuseport` to bypass Python 3.13's strict UDP port-binding restrictions on Windows, preventing core crashes without modifying 3rd-party dependencies.
- **Coroutine Resolution:** Removed erroneous `await` keywords on synchronous `.write()` methods, resolving `NoneType` execution failures.