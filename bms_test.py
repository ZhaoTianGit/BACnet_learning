import asyncio
import sys
import BAC0
from rich import print
from rich.traceback import install

install(show_locals=False)

if sys.platform == 'win32':
    import asyncio.base_events
    asyncio.base_events._set_reuseport = lambda sock: None
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    print("[bold magenta]Initializing Testbench (Sniper Mode v6 - WhoIs First)...[/bold magenta]")

    bacnet = BAC0.lite(ip='192.168.100.200', port=47810)
    await asyncio.sleep(3)

    target_ip   = '192.168.100.183:52025'
    DEVICE_ID   = 3506259   # confirmed from Yabe
    OBJ         = 'analogValue 0'

    try:
        # ── STEP 0: Discover & Register the Device ──────────────────────────────
        # This is the missing step — BAC0 must know the device exists before
        # it can address WriteProperty / ReadProperty to it.
        print(f"\n[cyan]--- Step 0: WhoIs → discovering device {DEVICE_ID} ---[/cyan]")
        bacnet.whoIs(
            low_limit=DEVICE_ID,
            high_limit=DEVICE_ID,
            destination=target_ip   # unicast directly, no broadcast needed
        )
        await asyncio.sleep(3)      # wait for IAm to come back and register

        # Confirm the device was registered
        devices_found = bacnet.discoveredDevices
        print(f"[cyan]  Discovered devices: {devices_found}[/cyan]")

        if not devices_found:
            print("[bold red]  ⚠ No devices discovered! Check subnet routing below.[/bold red]")
            print("[yellow]  Run: ping 192.168.100.183  ← from your terminal[/yellow]")
            print("[yellow]  If that fails, the two NICs can't talk — see routing fix below.[/yellow]")
            return

        # ── STEP 1: Write Out Of Service ─────────────────────────────────────────
        print(f"\n[yellow][Write 1][/yellow] outOfService → True ...")
        bacnet.write(f'{target_ip} {OBJ} outOfService True')
        await asyncio.sleep(3)

        # ── STEP 2: Confirm Out Of Service landed ────────────────────────────────
        oos = await bacnet.read(f'{target_ip} {OBJ} outOfService')
        print(f"[blue]  outOfService readback = [bold]{oos}[/bold][/blue]")
        if not oos:
            print("[bold red]  ⚠ outOfService still False — write did not land![/bold red]")
            return

        # ── STEP 3: Inject test vector ───────────────────────────────────────────
        print(f"[yellow][Write 2][/yellow] presentValue → 31 @ priority 8 ...")
        bacnet.write(f'{target_ip} {OBJ} presentValue 31 - 8')
        await asyncio.sleep(3)

        # ── STEP 4: Verify ───────────────────────────────────────────────────────
        result = await bacnet.read(f'{target_ip} {OBJ} presentValue')
        print(f"[blue][Read][/blue] presentValue = [bold green]{result} °C[/bold green]")

        if result == 31.0:
            print("\n[bold black on green] ✅ SUCCESS — T Set is now 31°C! [/bold black on green]")
        else:
            print(f"\n[bold yellow] ⚠ Got {result}, expected 31. Priority array may need relinquishing. [/bold yellow]")

    except Exception as e:
        print(f"[bold white on red] Fatal [/bold white on red] {e}")
    finally:
        bacnet.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
