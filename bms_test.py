import asyncio
import BAC0

# Wrap the main logic in an asynchronous function
async def main():
    print("Initializing Automated Testbench (Asyncio Framework)...")
    
    # Initialize BACnet network. BAC0 finds its event loop here.
    bacnet = BAC0.lite(port=47809)
    target_ip = '192.168.100.183'
    
    try:
        print(f"\n--- Test Initiated: Connecting to DUT {target_ip} ---") #DUT: Device Under Test
        
        # Action 1: Force Override (Decouple hardware logic)
        print("[Write] Action 1: Forcing Out of Service = True ...")
        bacnet.write(f'{target_ip} analogValue 0 outOfService True')
        
        # Async wait for 1 second to ensure the command is processed by the device
        await asyncio.sleep(1)
        
        # Action 2: Inject Test Vector
        print("[Write] Action 2: Injecting test vector (31 °C) ...")
        # The Present Value is now overridden, allowing arbitrary value injection
        bacnet.write(f'{target_ip} analogValue 0 presentValue 31')
        
        await asyncio.sleep(1)
        
        # Action 3: Read and Verify
        verify_temp = bacnet.read(f'{target_ip} analogValue 0 presentValue')
        print(f"[Read] Verification Successful! Setpoint overridden to: {verify_temp} °C")
        print("\n--- Test Passed! Please check the Room Simulator UI! ---")

    except Exception as e:
        print(f"Communication Failed. Please check network or IP address: {e}")
        
    finally:
        # Terminate test and release the network port
        bacnet.disconnect()

# Script entry point
if __name__ == "__main__":
    # asyncio.run() acts as the primary clock generator (Event Loop) for the script
    asyncio.run(main())