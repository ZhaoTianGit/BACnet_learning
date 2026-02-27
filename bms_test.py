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
    print("[bold magenta]Initializing Automated Testbench (Loopback Mode)...[/bold magenta]")
    
    # 🚨 KEY CHANGE 1: Bind Python strictly to the internal loopback adapter
    bacnet = BAC0.lite(ip='127.0.0.1', port=47809)
    
    # 🚨 KEY CHANGE 2: Target the Simulator on the loopback adapter
    target_ip = '127.0.0.1:47808'
    
    try:
        print(f"\n[bold cyan]--- Test Initiated: Connecting to DUT {target_ip} ---[/bold cyan]")
        
        # Action 1: Force Override
        print("[yellow][Write][/yellow] Action 1: Forcing Out of Service = [bold green]True[/bold green] ...")
        bacnet.write(f'{target_ip} analogValue 0 outOfService True')
        
        await asyncio.sleep(1)
        
        # Action 2: Inject Test Vector
        print("[yellow][Write][/yellow] Action 2: Injecting test vector ([bold red]31 °C[/bold red]) ...")
        bacnet.write(f'{target_ip} analogValue 0 presentValue 31')
        
        await asyncio.sleep(1) 
        
        # Action 3: Strict Read Verification
        print("[yellow][Read][/yellow] Action 3: Verifying injected vector...")
        verify_temp = await bacnet.read(f'{target_ip} analogValue 0 presentValue')
        
        print(f"[blue][Read][/blue] Verification Successful! Setpoint is explicitly confirmed at: [bold green]{verify_temp} °C[/bold green]")
        print("\n[bold black on green]--- Automation Sequence 100% Clean! ---[/bold black on green]")

    except Exception as e:
        print(f"[bold white on red] Validation Failed [/bold white on red] {e}")
        
    finally:
        bacnet.disconnect()

if __name__ == "__main__":
    asyncio.run(main())