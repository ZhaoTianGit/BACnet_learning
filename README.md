# Automated BACnet Commissioning & Testing Framework

![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)
![Protocol](https://img.shields.io/badge/Protocol-BACnet%2FIP-green.svg)
![Library](https://img.shields.io/badge/Library-bacpypes3-orange.svg)
![Status](https://img.shields.io/badge/Status-Working-brightgreen.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)

## 📌 Project Overview

This repository contains an asynchronous Python-based automation framework for testing and commissioning Building Management System (BMS) and Data Center HVAC edge devices over BACnet/IP.

By leveraging `bacpypes3` at the network layer, this script replaces traditional manual point-to-point testing (via UI/mouse clicks) with programmatic, scalable protocol validation. It demonstrates how to interact with industrial controllers at the BACnet application layer — specifically focusing on hardware override mechanisms, priority-based value injection, and read-back verification.

> **Validated against:** RoomController.Simulator (Device ID: 3506259) — successfully wrote `SetPoint.Value (AV:0) = 31.0 °C` ✅

---

## 🚀 Key Features & Validation Methodology

Coming from a strict system-level validation background, this tool treats physical MEP (Mechanical, Electrical, and Plumbing) hardware as the **Device Under Test (DUT)**:

- **Direct BACnet/IP Targeting:** Uses `bacpypes3` `NormalApplication` with an explicit `Address('IP:port')` to bypass the WhoIs/IAm discovery handshake — essential when the DUT runs on a non-standard dynamic port.
- **Hardware Decoupling / Force Override:** Implements the BACnet `Out-Of-Service` property to safely decouple control logic from physical sensors before injecting test values.
- **Priority-Based Write (WriteProperty):** Writes to commandable objects at **Priority 8 (Manual Operator)** — the industry-standard level for commissioning and test injection.
- **Read-Back Verification (ReadProperty):** Programmatically confirms injected values were accepted by reading back the `present-value` property after each write.
- **Automated State Restore:** Restores `Out-Of-Service = False` after testing — critical for safe operation on live hardware.
- **Asynchronous Architecture:** Built on `asyncio` for non-blocking network I/O, scalable to polling thousands of IO points across a large Data Center floor.

---

## 🛠️ Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Language | Python 3.13 | Windows-compatible with monkey patch |
| BACnet Engine | [bacpypes3 v0.0.104](https://github.com/JoelBender/BACpypes3) | Direct APDU control, no discovery required |
| High-level wrapper | [BAC0 v2025.09.15](https://bac0.readthedocs.io/) | Used for logging/task infrastructure |
| DUT Simulator | [Yabe + BACnet Room Simulator](https://sourceforge.net/projects/yetanotherbacnetexplorer/) | Local device emulation |
| Packet Analysis | Wireshark 4.6 | UDP-level verification |

---

## ⚙️ Prerequisites & Setup

### 1. Clone the repository
```bash
git clone <your-github-repo-url>
cd <your-repo-folder>
```

### 2. Install dependencies
```bash
pip install BAC0 bacpypes3 rich
```

### 3. Windows Firewall — open BACnet UDP ports (run once as Admin)
```powershell
New-NetFirewallRule -DisplayName "BACnet IN"  -Direction Inbound  -Protocol UDP -LocalPort 47808,47810 -Action Allow
New-NetFirewallRule -DisplayName "BACnet OUT" -Direction Outbound -Protocol UDP -LocalPort 47808,47810 -Action Allow
```

### 4. Configure target device
Before running, open **Yabe** and verify:
- The DUT's **current port** (dynamic — changes on every simulator restart)
- The **object instance number** of your target setpoint (check Name/Description in Properties panel)

Update these two lines in `bms_test.py`:
```python
TARGET = Address("192.168.100.183:52025")   # ← your DUT IP:port from Yabe
OBJ    = ObjectIdentifier("analog-value,0") # ← your target object
```

---

## 🏃 Usage

```bash
python bms_test.py
```

Expected output:
```
[Write 1] outOfService → True ...   ✅ ACKed
[Write 2] presentValue → 31 @ priority 8 ...   ✅ ACKed
[Read]  Verified: 31.0 °C
```

---

## 🔬 How It Works

### The Out-Of-Service Override Pattern
This is the standard BACnet testbench technique for injecting arbitrary values without physical hardware:

```
Step 1: Write out-of-service = True      → disconnects hardware input from PV
Step 2: Write present-value = X @ P8    → injects your test vector
Step 3: Read present-value               → verifies write was accepted
Step 4: Write out-of-service = False     → restores normal hardware operation
```

### BACnet Priority Array
Commandable objects use a 16-level priority array. Writes without a priority are silently rejected by most devices. Priority 8 (Manual Operator) is the industry standard for commissioning:

```
Priority 1  →  Manual Life Safety    (highest)
Priority 8  →  Manual Operator       ← used here
Priority 16 →  Default / Fallback    (lowest)
```

### Why bacpypes3 Direct Mode?
BAC0's built-in discovery broadcasts WhoIs on port **47808**. Software simulators running on dynamic ports (e.g. 52025) never hear this broadcast, causing silent write failures. Using `bacpypes3.NormalApplication` with an explicit `Address` bypasses discovery entirely — packets go directly to the DUT's IP:port with no handshake required.

---

## 🧩 Architecture

```
┌─────────────────────────────────────────────────────┐
│                  bms_test.py                        │
│                                                     │
│  asyncio.run(main())                                │
│       │                                             │
│       ▼                                             │
│  NormalApplication                                  │
│  bound to 192.168.100.183:47810                     │
│       │                                             │
│       │  UDP WritePropertyRequest                   │
│       ▼                                             │
│  Address("192.168.100.183:52025")  ←── DUT port     │
│       │                             from Yabe       │
│       ▼                                             │
│  RoomController.Simulator                           │
│  Device ID: 3506259                                 │
│  analogValue:0  (SetPoint.Value)                    │
└─────────────────────────────────────────────────────┘
```

---

## ⚠️ Known Platform Issues & Workarounds

### Python 3.13 on Windows — `reuse_port` crash
`bacpypes3` internally calls `create_datagram_endpoint(reuse_port=True)`, which is not supported on Windows. Apply this monkey patch **before any bacpypes3 import**:

```python
if sys.platform == 'win32':
    import asyncio.base_events
    asyncio.base_events._set_reuseport = lambda sock: None
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```

### Same-machine UDP routing
When Python and the BACnet simulator share the same IP, Windows drops self-addressed UDP packets. The fix is to bind Python to the same IP but a **different port** from the DUT (47810 vs 52025). Same-IP different-port UDP is allowed by Windows.

---

## 📁 Repository Structure

```
.
├── bms_test.py               # Main testbench script
├── BACNET_LEARNING_LOG.md    # Detailed debug journal and concept notes
├── BACnet_Learning_Guide.docx # Full reference guide (BACnet + Python stack)
└── README.md
```

---

## 📚 Learning Resources

- [BAC0 Documentation](https://bac0.readthedocs.io/)
- [bacpypes3 GitHub](https://github.com/JoelBender/BACpypes3)
- [ASHRAE BACnet Standard 135-2020](https://www.ashrae.org/technical-resources/bookstore/bacnet)
- [Yabe — Yet Another BACnet Explorer](https://sourceforge.net/projects/yetanotherbacnetexplorer/)
- [BACnet International](https://www.bacnetinternational.org/)