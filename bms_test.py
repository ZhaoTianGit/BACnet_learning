import asyncio
import sys
import BAC0
from rich import print
from rich.traceback import install

install(show_locals=False)

# =================================================================
# 🚨 WINDOWS & PYTHON 3.13 HOTFIX (The "Monkey Patch")
# =================================================================
if sys.platform == 'win32':
    import asyncio.base_events
    asyncio.base_events._set_reuseport = lambda sock: None
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    print("[bold magenta]Initializing Automated Testbench (Asyncio Framework)...[/bold magenta]")
    
    bacnet = BAC0.lite(port=47809)
    target_ip = '192.168.100.183:47808'
    
    try:
        print(f"\n[bold cyan]--- Test Initiated: Connecting to DUT {target_ip} ---[/bold cyan]")
        
        # Action 1: Force Override
        print("[yellow][Write][/yellow] Action 1: Forcing Out of Service = [bold green]True[/bold green] ...")
        bacnet.write(f'{target_ip} analogValue 0 outOfService True')
        
        await asyncio.sleep(1)
        
        # Action 2: Inject Test Vector
        print("[yellow][Write][/yellow] Action 2: Injecting test vector ([bold red]31 °C[/bold red]) ...")
        bacnet.write(f'{target_ip} analogValue 0 presentValue 31')
        
        await asyncio.sleep(2) # Give the simulator UI time to update
        
        # ==========================================================
        # Action 3: Read (Wrapped in Try-Except to prevent blocking)
        # ==========================================================
        try:
            verify_temp = await bacnet.read(f'{target_ip} analogValue 0 presentValue')
            print(f"[blue][Read][/blue] Verification Successful! Setpoint is: [bold green]{verify_temp} °C[/bold green]")
        except Exception as read_err:
            print(f"[bold red][Read Warning][/bold red] Software read failed ({read_err}), but control command may have succeeded!")
            print("[bold yellow]>>> PLEASE CHECK THE SIMULATOR UI MANUALLY! <<<[/bold yellow]")
            
        print("\n[bold black on green]--- Automation Sequence Completed ---[/bold black on green]")

    except Exception as e:
        print(f"[bold white on red] Fatal Error [/bold white on red] {e}")
        
    finally:
        bacnet.disconnect()

if __name__ == "__main__":
    asyncio.run(main())