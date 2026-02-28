# 🏢 BACnet Automation Testbench — Enterprise Edition Milestone

<div align="center">

![Date](https://img.shields.io/badge/Date-2026--03--01-blue.svg)
![Architecture](https://img.shields.io/badge/Architecture-Hybrid%20Native-purple.svg)
![Reliability](https://img.shields.io/badge/Reliability-Production%20Ready-brightgreen.svg)
![Safety](https://img.shields.io/badge/Safety-Fail--Safe%20Enabled-red.svg)

**Objective:** Transform a functional BACnet script into a robust, production-ready BMS hardware validation tool.

</div>

---

## 🗺️ Milestone Overview

This milestone marks the transition from a basic communication script to an **Enterprise-Grade Validation Tool**. The architecture now prioritizes hardware safety, deterministic network routing, and audit-ready logging, adhering to strict MNC software engineering standards.

---

## 🛡️ The 7 Pillars of Enterprise Hardening

| # | Architecture Upgrade | Technical Implementation | Business / Safety Value |
|---|----------------------|--------------------------|-------------------------|
| **1** | **Configuration Isolation** | Extracted `TARGET_PORT`, `TEST_VALUE`, and IPs to a top-level Config block. | Field engineers can run and target new devices without modifying core test logic. |
| **2** | **Deterministic Routing** | Replaced `0.0.0.0` socket binding with explicit `LOCAL_IP` targeting. | Prevents multi-NIC servers from silently routing BACnet traffic through incorrect VLANs. |
| **3** | **State Gating (Verification)** | Script reads `out-of-service` status *before* injecting the test vector. | Prevents injecting test values into live hardware if the decoupling command was rejected. |
| **4** | **The Dead Man's Switch** | `safe_restore_oos()` enforced within a strict `finally` exception-handling block. | **CRITICAL:** Guarantees physical controllers are never abandoned in a manual override state, preventing thermal runaway incidents. |
| **5** | **Audit-Ready Logging** | Implemented `log_step(step, action, detail)` with millisecond timestamps. | Generates parseable execution logs required for compliance in regulated industries (Data Centers, Pharma). |
| **6** | **Floating-Point Tolerance** | Replaced strict `==` with `abs(result - target) < 0.01` tolerance check. | Accounts for standard IEEE 754 precision loss during BACnet APDU round-trip serialization. |
| **7** | **Graceful UI Fallbacks** | Wrapped the `rich` library import in a `try...except ImportError` block. | Ensures the tool executes flawlessly on locked-down production servers lacking third-party dependencies. |

---

## 🔄 The Fail-Safe Execution Flow

The core sequence now strictly adheres to hardware decoupling safety standards:

```mermaid
graph TD;
    A[Bind Native Socket] --> B[Write Out-Of-Service = True];
    B --> C{Read-Back OOS == True?};
    C -- Yes --> D[Inject Test Vector @ Priority 8];
    C -- No --> E[Raise RuntimeError];
    D --> F[Read-Back & Verify Vector];
    F --> G;
    E --> G[FINALLY BLOCK: safe_restore_oos];
    G --> H[Write Out-Of-Service = False];
    H --> I[Close Socket Gracefully];