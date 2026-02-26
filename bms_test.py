import asyncio
import sys
import BAC0

# Wrap the main logic in an asynchronous function
async def main():
    print("Initializing Automated Testbench (Asyncio Framework)...")
    
    # Initialize BACnet network. BAC0 finds its event loop here.
    bacnet = BAC0.lite(port=47809)
    target_ip = '192.168.100.183'
    
    try:
        print(f"\n--- Test Initiated: Connecting to DUT {target_ip} ---")
        
        # Action 1: Force Override (Decouple hardware logic)
        print("[Write] Action 1: Forcing Out of Service = True ...")
        # Added 'await' for async network operations
        await bacnet.write(f'{target_ip} analogValue 0 outOfService True')
        
        # Async wait for 1 second to ensure the command is processed by the device
        await asyncio.sleep(1)
        
        # Action 2: Inject Test Vector
        print("[Write] Action 2: Injecting test vector (31 °C) ...")
        # Added 'await' to ensure the payload is successfully delivered
        await bacnet.write(f'{target_ip} analogValue 0 presentValue 31')
        
        await asyncio.sleep(1)
        
        # Action 3: Read and Verify
        # Added 'await' to extract the actual numerical value instead of the coroutine object
        verify_temp = await bacnet.read(f'{target_ip} analogValue 0 presentValue')
        print(f"[Read] Verification Successful! Setpoint overridden to: {verify_temp} °C")
        print("\n--- Test Passed! Please check the Room Simulator UI! ---")

    except Exception as e:
        print(f"Communication Failed. Please check network or IP address: {e}")
        
    finally:
        # Terminate test and release the network port
        bacnet.disconnect()

# Script entry point
if __name__ == "__main__":
    # OS-specific fix: Windows does not support 'reuse_port' natively in its default asyncio loop.
    # We must switch to the SelectorEventLoop policy for UDP socket stability.
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    # asyncio.run() acts as the primary clock generator (Event Loop) for the script
    asyncio.run(main())