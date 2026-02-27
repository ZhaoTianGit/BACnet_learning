import asyncio
import sys

if sys.platform == 'win32':
    import asyncio.base_events
    asyncio.base_events._set_reuseport = lambda sock: None
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from bacpypes3.ipv4.app import NormalApplication
from bacpypes3.local.device import DeviceObject
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import Real, Boolean, ObjectIdentifier
from bacpypes3.basetypes import PropertyIdentifier
from rich import print

TARGET = Address("192.168.100.183:52025")

# ── FIX: Use ObjectIdentifier object, not a tuple ────────────────────────────
OBJ_ID = ObjectIdentifier("analog-value,0")

async def main():
    print("[bold magenta]bacpypes3 Direct Mode (v14)...[/bold magenta]")

    device = DeviceObject(
        objectIdentifier=("device", 9999),
        objectName="TestBench",
        vendorIdentifier=999,
    )
    app = NormalApplication(device, Address("192.168.100.183:47810"))
    await asyncio.sleep(1)

    try:
        # ── Write 1: outOfService ─────────────────────────────────────────────
        print("\n[yellow][Write 1][/yellow] outOfService → True ...")
        await app.write_property(
            TARGET, OBJ_ID,
            PropertyIdentifier("out-of-service"),
            Boolean(True),
        )
        print("[green]  ✅ Write 1 ACKed![/green]")
        await asyncio.sleep(1)

        # ── Write 2: presentValue @ priority 8 ───────────────────────────────
        print("[yellow][Write 2][/yellow] presentValue → 31 @ priority 8 ...")
        await app.write_property(
            TARGET, OBJ_ID,
            PropertyIdentifier("present-value"),
            Real(31.0),
            priority=8,
        )
        print("[green]  ✅ Write 2 ACKed![/green]")
        await asyncio.sleep(1)

        # ── Read back ─────────────────────────────────────────────────────────
        print("[blue][Read][/blue] presentValue ...")
        result = await app.read_property(
            TARGET, OBJ_ID,
            PropertyIdentifier("present-value"),
        )
        print(f"[blue]  Result: [bold green]{result} °C[/bold green][/blue]")

        if float(result) == 31.0:
            print("\n[bold black on green] ✅ SUCCESS — T Set is now 31°C! [/bold black on green]")

    except Exception as e:
        print(f"[bold white on red] Fatal [/bold white on red] {e}")
        import traceback
        traceback.print_exc()
    finally:
        app.close()

if __name__ == "__main__":
    asyncio.run(main())