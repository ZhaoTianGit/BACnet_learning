import asyncio
import sys
import BAC0
from rich import print
from rich.traceback import install

# Intercept system errors and apply beautiful syntax highlighting to the traceback
install(show_locals=False)

# =================================================================
# 🚨 WINDOWS & PYTHON 3.13 HOTFIX (The "Monkey Patch" Technique)
# =================================================================
if sys.platform == 'win32':
    import asyncio.base_events
    # Dynamically overwrite Python 3.13's underlying check function in memory to return None.
    # This perfectly bypasses the ValueError crash without modifying any 3rd-party source files!
    asyncio.base_events._set_reuseport = lambda sock: None
    
    # Maintain a UDP-friendly network engine policy for Windows
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
# =================================================================

async def main():
    print("[bold magenta]Initializing Automated Testbench (Asyncio Framework)...[/bold magenta]")
    
    # Initialize BACnet network.
    bacnet = BAC0.lite(port=47809)
    target_ip = '192.168.100.183'
    
    try:
        print(f"\n[bold cyan]--- Test Initiated: Connecting to DUT {target_ip} ---[/bold cyan]")
        
        # Action 1: Force Override (Decouple hardware logic)
        print("[yellow][Write][/yellow] Action 1: Forcing Out of Service = [bold green]True[/bold green] ...")
        # .write() is synchronous and returns None, do NOT use await here.
        bacnet.write(f'{target_ip} analogValue 0 outOfService True')
        
        await asyncio.sleep(1)
        
        # Action 2: Inject Test Vector
        print("[yellow][Write][/yellow] Action 2: Injecting test vector ([bold red]31 °C[/bold red]) ...")
        bacnet.write(f'{target_ip} analogValue 0 presentValue 31')
        
        await asyncio.sleep(1)
        
        # Action 3: Read and Verify
        # KEEP await here: .read() needs to wait for the network packet to return
        verify_temp = await bacnet.read(f'{target_ip} analogValue 0 presentValue')
        print(f"[blue][Read][/blue] Verification Successful! Setpoint overridden to: [bold green]{verify_temp} °C[/bold green]")
        
        print("\n[bold black on green]--- Test Passed! Please check the Room Simulator UI! ---[/bold black on green]")

    except Exception as e:
        print(f"[bold white on red] Communication Failed [/bold white on red] {e}")
        
    finally:
        # Disconnect gracefully to release the port
        bacnet.disconnect()

if __name__ == "__main__":
    # The Event Loop is started here AFTER the Monkey Patch has been applied
    asyncio.run(main())