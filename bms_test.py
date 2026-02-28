"""
================================================================================
 BACnet Automated Commissioning Testbench
 Enterprise Edition — bacpypes3 Native Engine
================================================================================
 Protocol  : BACnet/IP (ASHRAE 135-2020)
 Transport : UDP/IPv4
 Library   : bacpypes3 v0.0.104

 Usage:
   1. Open Yabe and note the simulator's current dynamic port
   2. Update TARGET_PORT below
   3. Run:  python bms_test.py

 Safety:
   Out-Of-Service is ALWAYS restored in the finally block, even on exceptions.
   This prevents the controller from running on injected test values indefinitely.
================================================================================
"""

import asyncio
import sys
import logging
from datetime import datetime

# ── Rich (optional — graceful fallback if not installed) ─────────────────────
try:
    from rich import print
    from rich.traceback import install
    from rich.logging import RichHandler
    install(show_locals=False)
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)]
    )
    RICH_AVAILABLE = True
except ImportError:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    RICH_AVAILABLE = False

log = logging.getLogger("testbench")

# =============================================================================
# 🚨 WINDOWS + PYTHON 3.13 HOTFIX
# Must be applied BEFORE any bacpypes3 import.
# bacpypes3 internally calls create_datagram_endpoint(reuse_port=True),
# which is unsupported on Windows. This patch disables that call safely.
# =============================================================================
if sys.platform == "win32":
    import asyncio.base_events
    asyncio.base_events._set_reuseport = lambda sock: None
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from bacpypes3.ipv4.app import NormalApplication
from bacpypes3.local.device import DeviceObject
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import Real, Boolean, ObjectIdentifier
from bacpypes3.basetypes import PropertyIdentifier

# =============================================================================
# ⚙️  CONFIGURATION
# Update TARGET_PORT every time the simulator or Yabe restarts.
# The simulator assigns a new ephemeral port on each launch.
# =============================================================================

# ── DUT (Device Under Test) ───────────────────────────────────────────────────
TARGET_IP       = "192.168.100.183"
TARGET_PORT     = 63205          # ⚠ Update from Yabe after every simulator restart
TARGET          = Address(f"{TARGET_IP}:{TARGET_PORT}")

# ── BACnet Object to test ─────────────────────────────────────────────────────
OBJ_ID          = ObjectIdentifier("analog-value,0")   # AV:0 = SetPoint.Value
TEST_VALUE      = 31.0           # °C — the value to inject
WRITE_PRIORITY  = 8              # Priority 8 = Manual Operator (ASHRAE standard for commissioning)

# ── Local testbench NIC ───────────────────────────────────────────────────────
# Use the explicit BACnet-designated NIC IP, NOT 0.0.0.0.
# On multi-NIC servers (common in data centers), 0.0.0.0 lets the OS pick the
# interface, which may silently route BACnet traffic through the wrong VLAN.
LOCAL_IP        = "192.168.100.183"
LOCAL_PORT      = 47810          # Must differ from TARGET_PORT and 47808

# ── Testbench BACnet device identity ─────────────────────────────────────────
DEVICE_ID       = 9999           # Must be unique on the BACnet network
DEVICE_NAME     = "PY-Testbench"
VENDOR_ID       = 999

# ── Timing ────────────────────────────────────────────────────────────────────
SOCKET_BIND_DELAY   = 1.0        # seconds — wait for OS to bind UDP socket
POST_WRITE_DELAY    = 1.0        # seconds — allow controller to process write
VERIFY_READ_DELAY   = 2.0        # seconds — wait before read-back verification
READ_TOLERANCE      = 0.01       # floating-point comparison tolerance

## In industry you hand scripts to field engineers who should never need to touch the logic — only the config block at the top.##

# =============================================================================
# 🔧  HELPER FUNCTIONS
# =============================================================================

def log_step(step: int, action: str, detail: str) -> None:
    """Structured step logger for audit trail."""
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    log.info(f"[{ts}] STEP {step} | {action} | {detail}")


async def safe_restore_oos(app: NormalApplication) -> None:
    """
    Restore Out-Of-Service (OOS) = False unconditionally.
    Called in finally block to guarantee hardware is never left in override state.
    Critical safety function — do not remove.
    """
    try:
        log.info("RESTORE | out-of-service → False (safety restore)")
        await asyncio.sleep(30) # delay to ensure any pending writes have settled before restore 
        #<-- can be adjusted or removed based on observed controller behavior, but a short delay 
        #is often prudent to avoid race conditions where the controller is still processing the 
        # test write when we attempt to restore OOS.
        ## delay for me to read from the console
        await app.write_property(
            TARGET, OBJ_ID,
            PropertyIdentifier("out-of-service"),
            Boolean(False),
        )
        log.info("RESTORE | ✅ Out-Of-Service successfully restored to False")
    except Exception as restore_err:
        # Log as CRITICAL — a human must manually verify the controller state
        log.critical(
            f"RESTORE FAILED — Out-Of-Service may still be True on {TARGET}!\n"
            f"Error: {restore_err}\n"
            f"ACTION REQUIRED: Manually verify controller state in Yabe immediately."
        )


# =============================================================================
# 🚀  MAIN TEST SEQUENCE
# =============================================================================

async def run_test(app: NormalApplication) -> bool:
    """
    Execute the BACnet override test sequence.
    Returns True on full pass, False on any failure.
    Raises exceptions to the caller for finally-block handling.
    """
    print(f"\n[bold cyan]{'─'*60}[/bold cyan]")
    print(f"[bold cyan] BACnet Testbench — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/bold cyan]")
    print(f"[bold cyan] DUT   : {TARGET}[/bold cyan]")
    print(f"[bold cyan] Object: {OBJ_ID}   Priority: {WRITE_PRIORITY}[/bold cyan]")
    print(f"[bold cyan]{'─'*60}[/bold cyan]\n")

    # ── STEP 1: Decouple hardware (Out-Of-Service = True) ─────────────────────
    log_step(1, "WRITE", f"out-of-service → True  (hardware decoupled)")
    await app.write_property(
        TARGET, OBJ_ID,
        PropertyIdentifier("out-of-service"),
        Boolean(True),
    )
    print("[green]  ✅ Step 1 ACKed — hardware decoupled[/green]")
    await asyncio.sleep(POST_WRITE_DELAY)

    # ── STEP 2: Verify Out-Of-Service landed ──────────────────────────────────
    log_step(2, "READ", "verifying out-of-service = True before injection")
    oos_status = await app.read_property(
        TARGET, OBJ_ID,
        PropertyIdentifier("out-of-service"),
    )
    if not oos_status:
        raise RuntimeError(
            "STEP 2 FAILED: out-of-service did not assert True. "
            "Controller may have rejected the write — check priority array or object permissions."
        )
    print(f"[green]  ✅ Step 2 Confirmed — out-of-service = {oos_status}[/green]")
    await asyncio.sleep(POST_WRITE_DELAY)

    # ── STEP 3: Inject test vector ────────────────────────────────────────────
    log_step(3, "WRITE", f"present-value → {TEST_VALUE} °C @ priority {WRITE_PRIORITY}")
    await app.write_property(
        TARGET, OBJ_ID,
        PropertyIdentifier("present-value"),
        Real(TEST_VALUE),
        priority=WRITE_PRIORITY,
    )
    print(f"[green]  ✅ Step 3 ACKed — {TEST_VALUE} °C injected[/green]")
    await asyncio.sleep(VERIFY_READ_DELAY)

    # ── STEP 4: Read back and verify ──────────────────────────────────────────
    log_step(4, "READ", "read-back verification of present-value")
    result = await app.read_property(
        TARGET, OBJ_ID,
        PropertyIdentifier("present-value"),
    )
    print(f"[blue]  Read-back: [bold green]{result} °C[/bold green][/blue]")

    if abs(float(result) - TEST_VALUE) > READ_TOLERANCE:
        raise AssertionError(
            f"STEP 4 FAILED: Expected {TEST_VALUE} °C, got {result} °C. "
            f"Delta = {abs(float(result) - TEST_VALUE):.4f}. "
            f"Check if a higher-priority source is overriding priority {WRITE_PRIORITY}."
        )

    print(f"\n[bold black on green] ✅ PASS — All 4 steps completed. DUT responded correctly. [/bold black on green]")
    return True


async def main() -> None:
    print("[bold magenta]Initializing BACnet Testbench (Enterprise Edition)...[/bold magenta]")

    # ── Instantiate local BACnet device and bind UDP socket ───────────────────
    device = DeviceObject(
        objectIdentifier=("device", DEVICE_ID),
        objectName=DEVICE_NAME,
        vendorIdentifier=VENDOR_ID,
    )
    app = NormalApplication(device, Address(f"{LOCAL_IP}:{LOCAL_PORT}"))
    log.info(f"Bound to {LOCAL_IP}:{LOCAL_PORT} | Targeting {TARGET}")
    await asyncio.sleep(SOCKET_BIND_DELAY)

    oos_was_asserted = False  # track whether we need to restore OOS

    try:
        # Pre-check: read current OOS state so we know what to restore
        initial_oos = await app.read_property(
            TARGET, OBJ_ID, PropertyIdentifier("out-of-service")
        )
        log.info(f"Pre-test | out-of-service baseline = {initial_oos}")

        oos_was_asserted = True   # from this point, we may write OOS=True
        await run_test(app)

    except (RuntimeError, AssertionError) as test_err:
        print(f"\n[bold white on red] TEST FAILED [/bold white on red] {test_err}")

    except Exception as unexpected_err:
        print(f"\n[bold white on red] UNEXPECTED ERROR [/bold white on red] {unexpected_err}")
        import traceback
        traceback.print_exc()

    finally:
        # ── Safety restore: always bring OOS back to False ────────────────────
        if oos_was_asserted:
            await safe_restore_oos(app)

        # ── Release UDP socket ────────────────────────────────────────────────
        app.close()
        print("[dim]Sockets closed. Testbench terminated.[/dim]")


# =============================================================================
if __name__ == "__main__":
    asyncio.run(main())