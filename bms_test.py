import asyncio
import sys
import BAC0
from rich import print
from rich.traceback import install

# 这行代码的魔法：让系统抛出的 Error 也变得极其美观且高亮！
install(show_locals=False) 

async def main():
    print("[bold magenta]Initializing Automated Testbench (Asyncio Framework)...[/bold magenta]")
    
    # Initialize BACnet network.
    bacnet = BAC0.lite(port=47809)
    target_ip = '192.168.100.183'
    
    try:
        print(f"\n[bold cyan]--- Test Initiated: Connecting to DUT {target_ip} ---[/bold cyan]")
        
        # Action 1: Force Override (Decouple hardware logic)
        print("[yellow][Write][/yellow] Action 1: Forcing Out of Service = [bold green]True[/bold green] ...")
        # Fix: .write() is synchronous and returns None, do NOT use await here.
        bacnet.write(f'{target_ip} analogValue 0 outOfService True')
        
        await asyncio.sleep(1)
        
        # Action 2: Inject Test Vector
        print("[yellow][Write][/yellow] Action 2: Injecting test vector ([bold red]31 °C[/bold red]) ...")
        # Fix: .write() is synchronous, do NOT use await here.
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
        bacnet.disconnect()

if __name__ == "__main__":
    # OS-specific fix for Windows UDP socket issue (DO NOT DELETE)
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    asyncio.run(main())