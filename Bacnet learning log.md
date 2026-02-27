# 📡 BACnet Automation Testbench — Learning Log

<div align="center">

![Date](https://img.shields.io/badge/Date-2026--02--28-blue.svg)
![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![BAC0](https://img.shields.io/badge/BAC0-v2025.09.15-orange.svg)
![bacpypes3](https://img.shields.io/badge/bacpypes3-v0.0.104-orange.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![Status](https://img.shields.io/badge/Mission-Accomplished%20✅-brightgreen.svg)

**Objective:** Automate BACnet `WriteProperty` to inject `T Set = 31°C` into a Room Control Simulator (DUT)

</div>

---

## 🗺️ What's Inside This Log

| Section | Coverage |
|---------|----------|
| [🏆 Final Result](#-final-result) | Terminal output proving success |
| [🧠 BACnet Fundamentals](#-bacnet-concepts-learned) | Object model, Priority Array, Out Of Service pattern |
| [🌐 Network Layer](#-network-layer) | Port architecture, WhoIs/IAm, Windows loopback problem, Firewall rules |
| [🐍 Python Stack](#-python-stack) | BAC0 vs bacpypes3, monkey patch, sync vs async API, write syntax |
| [🐛 Bugs & Fixes](#-bugs-encountered--fixes) | All 8 errors hit during the session with root causes |
| [🛠 Skills Acquired](#-skills-acquired) | Python/async, BACnet, networking, tooling |
| [🔬 Debugging Toolkit](#-debugging-toolkit) | Wireshark workflow, Yabe inspection, runtime introspection |
| [📋 Pre-Test Checklist](#-pre-test-checklist-industry-use) | 8-point industry commissioning checklist |
| [🚀 Final Working Script](#-final-working-script) | Production-ready template |
| [📚 References](#-references) | Docs, standards, tools |

---

## 🏆 Final Result

> Successfully wrote `presentValue = 31.0 °C` to `analogValue:0` (SetPoint.Value)  
> on **Device 3506259** via `bacpypes3` direct mode — no discovery required.

```
[Write 1] outOfService → True ...             ✅ ACKed
[Write 2] presentValue → 31 @ priority 8 ...  ✅ ACKed
[Read]    Result: 31.0 °C                     ✅ SUCCESS
```

---

## 🧠 BACnet Concepts Learned

### 📦 Object Model
> BACnet exposes device data as **Objects** with **Properties**. You never write raw memory addresses.

| Object Type | Code | Typical Use | Example |
|------------|------|-------------|---------|
| Analog Input `AI` | 0 | Read-only sensor | Temperature sensor |
| Analog Output `AO` | 1 | Writable actuator | Valve position |
| Analog Value `AV` | 2 | Writable setpoint | **T Set ← our target** |
| Binary Input `BI` | 3 | Read-only digital | Occupancy sensor |
| Binary Value `BV` | 5 | Writable on/off | Heater state |
| Multi-State Value `MV` | 19 | Enumerated states | Ventilation level |

- Every object has an **instance number** — always verify in Yabe, never assume instance `0`
- Object is referenced as `type,instance` → e.g. `analog-value,0`

---

### 🎯 Priority Array
> Commandable objects (`AO`, `AV`, `BV`) use a **16-level priority array**.  
> A write **without a priority is silently rejected** by most real devices and simulators.

```
Priority  1  ──  Manual Life Safety       (highest — fire/smoke)
Priority  2  ──  Automatic Life Safety
Priority  3-7 ── Reserved (critical BMS)
Priority  8  ──  Manual Operator          ← ✅ USE THIS for testing
Priority  9-15 ─ Supervisory / Scheduling
Priority 16  ──  Default / Fallback       (lowest)
```

**Rule:** Higher number = lower priority. `1` beats `16`. Always specify `priority=8` in test scripts.

---

### 🔧 Out Of Service Override Pattern
> The standard testbench technique to inject arbitrary values without physical hardware.

```
Step 1 ──► Write  out-of-service = True        # disconnects hardware input from PV
Step 2 ──► Write  present-value  = X @ P8      # injects your test vector
Step 3 ──► Read   present-value                # verifies write was accepted
Step 4 ──► Write  out-of-service = False        # ALWAYS restore — critical on live hardware
```

> [!WARNING]
> **Never skip Step 4 on real hardware.** Leaving `Out-Of-Service = True` means the controller
> runs on your injected fake value indefinitely, regardless of what the physical sensor reads.

---

### 📡 WhoIs / IAm Discovery
- BAC0 broadcasts `WhoIs` on **port 47808** before any read/write to register the device
- Software simulators on **dynamic ports** (e.g. `52025`) **never hear port 47808 broadcasts**
- This is why `BAC0.discover()` always returns `0 devices` for local simulators
- **Fix:** Use `bacpypes3` direct mode with explicit `Address('IP:port')` — no discovery needed

---

## 🌐 Network Layer

### Port Architecture

| Port | Role | Notes |
|------|------|-------|
| `47808` (0xBAC0) | Standard BACnet/IP | WhoIs always broadcasts here |
| `52025` (dynamic) | Simulator / DUT | **Changes every restart** — check Yabe each time |
| `47810` | Python testbench | Must differ from 47808 and DUT port |

### The Windows Same-IP UDP Problem
When Python and the simulator share the same IP (`192.168.100.183`), Windows drops self-addressed UDP packets at the network stack level.

```
❌ Ping works   → ICMP is handled differently from UDP
❌ BACnet fails → UDP self-addressed packets are silently dropped by Windows

✅ Fix: bind Python to same IP but DIFFERENT port (47810 vs 52025)
   Same-IP, different-port UDP is allowed by Windows
```

### Windows Firewall
> Firewall allows `ping` (ICMP) but **blocks UDP by default**. Must be explicitly opened:

```powershell
New-NetFirewallRule -DisplayName "BACnet IN"  -Direction Inbound  -Protocol UDP -LocalPort 47808,47810 -Action Allow
New-NetFirewallRule -DisplayName "BACnet OUT" -Direction Outbound -Protocol UDP -LocalPort 47808,47810 -Action Allow
New-NetFirewallRule -DisplayName "BACnet Sim" -Direction Inbound  -Protocol UDP -RemoteAddress 192.168.100.183 -Action Allow
```

---

## 🐍 Python Stack

### BAC0 vs bacpypes3 — When to Use Which

```
┌────────────────────────────────────────────────────────┐
│  BAC0 Lite (high-level)                                │
│  ✅ Good for: standard read/write when discovery works  │
│  ❌ Fails when: DUT is on a dynamic non-47808 port      │
├────────────────────────────────────────────────────────┤
│  bacpypes3 NormalApplication (low-level)               │
│  ✅ Good for: direct APDU control, no discovery needed  │
│  ✅ Use when: BAC0 discovery fails (our case)           │
└────────────────────────────────────────────────────────┘
```

### The Windows Monkey Patch
> Must be applied **before any `bacpypes3` import**. Import order is critical.

```python
if sys.platform == 'win32':
    import asyncio.base_events
    asyncio.base_events._set_reuseport = lambda sock: None        # ← patch
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Only import bacpypes3 AFTER the patch above
from bacpypes3.ipv4.app import NormalApplication
```

### BAC0 Lite Sync vs Async (v2025.09.15)

| Method | Type | How to Call |
|--------|------|-------------|
| `bacnet.write()` | **Sync** | `bacnet.write('...')` — no await |
| `bacnet.read()` | **Coroutine** | `await bacnet.read('...')` |
| `bacnet.who_is()` | **Coroutine** | `await bacnet.who_is(low_limit=X, high_limit=Y)` |
| `bacnet.discover()` | **Sync** | `bacnet.discover()` — no await |
| `bacnet._discover()` | **Coroutine** | `await bacnet._discover(...)` |

> **Runtime detection trick:**
> ```python
> import inspect
> inspect.iscoroutinefunction(bacnet.read)   # True → needs await
> inspect.isawaitable(result)                # True → returned coroutine, needs await
> ```

### BAC0 Write String Syntax
```
bacnet.write('<IP:PORT> <objectType> <instance> <property> <value> - <priority>')

# Example:
bacnet.write('192.168.100.183:52025 analogValue 0 presentValue 31 - 8')
#             └─────────────────┘   └──────────┘ └┘ └──────────┘ └┘ └┘
#             DUT IP:port           object type  #  property     val  P

# ⚠ Do NOT add "- priority" for non-commandable properties like outOfService
bacnet.write('192.168.100.183:52025 analogValue 0 outOfService True')
```

---

## 🐛 Bugs Encountered & Fixes

| # | Symptom | Root Cause | Fix |
|---|---------|-----------|-----|
| 1 | `ValueError: reuse_port not supported` | Python 3.13 Windows socket restriction | Monkey patch `_set_reuseport` **before** any bacpypes3 import |
| 2 | `Running one shot task _write` but value unchanged | BAC0 queues task but can't serialize without device registration | Switch to bacpypes3 direct mode |
| 3 | `Trouble with Iam... = []` on every read | WhoIs on port 47808 never reaches simulator on port 52025 | `app.read_property()` with explicit `Address` |
| 4 | `AbortPDU: no-response` | Packet left Python but simulator didn't ACK — wrong encoding | Use `write_property()` helper, not raw PDU construction |
| 5 | `coroutine '...' was never awaited` | BAC0 Lite mixes sync and async methods | Check with `inspect.iscoroutinefunction()` before calling |
| 6 | `NormalApplication() TypeError` | `local_address` must be `Address` object, not string | `Address('192.168.100.183:47810')` |
| 7 | Ping works but BACnet reads time out | Firewall allows ICMP, blocks UDP | Add explicit UDP rules via `New-NetFirewallRule` |
| 8 | Zero Wireshark packets on loopback adapter | Python routing via main NIC, not loopback | Capture on main Ethernet; bind Python to main NIC IP |

---

## 🛠 Skills Acquired

<details>
<summary><b>🐍 Python / Async</b></summary>

- Applying monkey patches before library imports — **import order is critical**
- `asyncio.WindowsSelectorEventLoopPolicy()` for Python 3.13 on Windows
- Using `inspect.iscoroutinefunction()` and `inspect.isawaitable()` to detect sync vs async at runtime
- Correctly calling sync methods inside an async context
- `asyncio.run(main())` provides the running event loop that BAC0 internally requires

</details>

<details>
<summary><b>📡 BACnet / bacpypes3</b></summary>

- Using `NormalApplication` + explicit `Address` for direct unicast BACnet/IP without discovery
- `ObjectIdentifier('analog-value,0')` — dash-separated string, not a tuple
- `PropertyIdentifier('out-of-service')` / `PropertyIdentifier('present-value')` — dash-separated, lowercase
- Primitive type wrappers: `Real(31.0)`, `Boolean(True)`
- `write_property()` helper vs raw `WritePropertyRequest` PDU construction

</details>

<details>
<summary><b>🌐 Networking / Debugging</b></summary>

- Wireshark **display filter** syntax: `||` not `or`, applied after capture starts (not on welcome screen)
- Capturing on the correct NIC — always use main Ethernet, not the loopback adapter
- Interpreting BACnet packet flow: `WritePropertyRequest` → `SimpleACK` ✅ vs `AbortPDU` ❌
- Windows Firewall: ICMP and UDP are handled independently — ping is not a reliable BACnet test
- PowerShell `New-NetFirewallRule` for programmatic firewall management

</details>

<details>
<summary><b>🔧 Tooling</b></summary>

- **Yabe:** reading current device port (dynamic — changes on every simulator restart), inspecting object instances, verifying property values after writes in the Properties panel
- `[m for m in dir(obj) if 'keyword' in m.lower()]` to explore unknown library APIs at runtime
- `inspect.signature(method)` to read method signatures when docs are wrong or missing

</details>

---

## 🔬 Debugging Toolkit

### Wireshark — Ground Truth

```
Step 1: Open Wireshark → double-click main Ethernet adapter (NOT loopback)
Step 2: Leave capture filter blank — start capturing immediately
Step 3: In the toolbar display filter bar, type:
        udp.port == 52025 || udp.port == 47810
Step 4: Run your script while capturing
Step 5: Interpret results ↓
```

| What You See | Diagnosis |
|---|---|
| Write packet + `SimpleACK` reply | ✅ Full success — both ends talking |
| Write packet + NO reply from DUT | Simulator rejecting — wrong port or encoding |
| Write packet + `AbortPDU` | Packet arrived, simulator NAK'd — check object/property names |
| **Zero packets matching filter** | Packets not leaving Python — check NIC binding or firewall |

### Yabe — Pre-Flight Inspection

Before every test run, verify in Yabe:
- **Current port** — hover over device node in left panel. Recheck after every simulator restart
- **Object instance number** — Objects list → Properties panel → check `Object Name` and `Description`
- **Present Value** — confirm baseline before writing
- **Out Of Service** — must be `False` before starting
- **Status Flags** — must be `0000` (no existing fault/override)

---

## 📋 Pre-Test Checklist (Industry Use)

```
Before every test session:

 □  Verify DUT IP and current port in Yabe  ← changes on every restart
 □  Confirm object instance number in Yabe Objects panel
 □  Check Out Of Service = False before starting
 □  Check Status Flags = 0000 (no existing fault or override)
 □  Confirm Python binding IP reachable:  ping <target_ip>
 □  Windows Firewall UDP rules in place for ports 47808 and 47810
 □  Wireshark filter ready:  udp.port == <dut_port> || udp.port == 47810

After every test session:

 □  Restore Out Of Service = False          ← CRITICAL on real hardware
 □  Verify Present Value returned to sensor reading (not injected value)
```

---

## 🚀 Final Working Script

```python
import asyncio
import sys

# ── Step 0: Monkey patch BEFORE any bacpypes3 import ─────────────────────────
if sys.platform == 'win32':
    import asyncio.base_events
    asyncio.base_events._set_reuseport = lambda sock: None
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from bacpypes3.ipv4.app import NormalApplication
from bacpypes3.local.device import DeviceObject
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import Real, Boolean, ObjectIdentifier
from bacpypes3.basetypes import PropertyIdentifier

# ── Config ────────────────────────────────────────────────────────────────────
TARGET = Address("192.168.100.183:52025")    # ⚠ verify port in Yabe first!
OBJ    = ObjectIdentifier("analog-value,0")  # ⚠ verify instance in Yabe!

async def main():
    device = DeviceObject(
        objectIdentifier=("device", 9999),
        objectName="TestBench",
        vendorIdentifier=999,
    )
    # Bind to same IP as DUT but different port — bypasses Windows same-IP block
    app = NormalApplication(device, Address("192.168.100.183:47810"))
    await asyncio.sleep(1)

    # ── Step 1: Override hardware ─────────────────────────────────────────────
    await app.write_property(TARGET, OBJ,
        PropertyIdentifier("out-of-service"), Boolean(True))

    # ── Step 2: Inject test vector @ Priority 8 ───────────────────────────────
    await app.write_property(TARGET, OBJ,
        PropertyIdentifier("present-value"), Real(31.0), priority=8)

    # ── Step 3: Read back and verify ──────────────────────────────────────────
    result = await app.read_property(TARGET, OBJ,
        PropertyIdentifier("present-value"))
    print(f"✅ Verified: {result} °C")

    # ── Step 4: Restore — ALWAYS do this on real hardware ─────────────────────
    await app.write_property(TARGET, OBJ,
        PropertyIdentifier("out-of-service"), Boolean(False))

    app.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📚 References

| Resource | Link | Notes |
|----------|------|-------|
| 📖 BAC0 Documentation | [bac0.readthedocs.io](https://bac0.readthedocs.io/) | High-level BACnet wrapper |
| 🐙 bacpypes3 GitHub | [github.com/JoelBender/BACpypes3](https://github.com/JoelBender/BACpypes3) | Low-level BACnet library used in final solution |
| 📐 ASHRAE BACnet Standard 135-2020 | [ashrae.org](https://www.ashrae.org/technical-resources/bookstore/bacnet) | Official protocol specification |
| 🔍 Yabe — BACnet Explorer | [sourceforge.net/projects/yabe](https://sourceforge.net/projects/yetanotherbacnetexplorer/) | Essential GUI inspection tool |
| 🌐 BACnet International | [bacnetinternational.org](https://www.bacnetinternational.org/) | Community & certification resources |

---

## 🤝 Acknowledgements

This learning session was completed with help from AI pair programming:

| Assistant | Role in This Session |
|-----------|---------------------|
| 🤖 [Claude](https://claude.ai) (Anthropic) | Primary debug partner — architecture decisions, error diagnosis, 14 script iterations |
| 🤖 [Gemini](https://gemini.google.com) (Google) | Secondary reference for BACnet protocol concepts |

> *"Debugging with a silicon mate is like having a senior engineer on call at 1am —  
> except they never get tired of your questions."*

---

<div align="center">

**Built with curiosity. Debugged with persistence.**

`14 script versions` · `1 Wireshark capture` · `1 working testbench` 🎉

</div>