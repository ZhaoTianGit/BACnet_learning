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
    print("[bold magenta]Initializing Testbench (Sniper Mode v4)...[/bold magenta]")

    # Loopback adapter IP — must be different from 192.168.100.183
    bacnet = BAC0.lite(ip='192.168.100.200', port=47810)

    # Give BAC0's internal async tasks time to fully initialize
    await asyncio.sleep(3)

    target_ip = '192.168.100.183:52025'
    OBJ = 'analogValue 0'

    try:
        print(f"\n[cyan]--- Test: {target_ip} | {OBJ} ---[/cyan]")

        # Step 1: Enable Out Of Service
        print("[yellow][Write][/yellow] outOfService → True ...")
        bacnet.write(f'{target_ip} {OBJ} outOfService True')
        await asyncio.sleep(2)

        # Step 2: Write present value with priority
        print("[yellow][Write][/yellow] presentValue → 31 @ priority 8 ...")
        bacnet.write(f'{target_ip} {OBJ} presentValue 31 - 8')
        await asyncio.sleep(2)

        # Step 3: Read back result
        try:
            result = bacnet.read(f'{target_ip} {OBJ} presentValue')
            print(f"[blue][Read][/blue] Result: [bold green]{result} °C[/bold green]")
        except Exception as e:
            print(f"[bold red][Read Failed][/bold red] {e}")
            print("[yellow]>>> Check Simulator UI — T Set should show 31 <<<[/yellow]")

        print("\n[bold black on green]--- Sequence Complete ---[/bold black on green]")

    except Exception as e:
        print(f"[bold white on red] Fatal [/bold white on red] {e}")
    finally:
        bacnet.disconnect()

if __name__ == "__main__":
    asyncio.run(main())  # This provides the running event loop BAC0 needs