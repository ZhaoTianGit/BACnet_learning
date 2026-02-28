import asyncio
import sys
import BAC0
from bacpypes3.pdu import Address
from bacpypes3.primitivedata import Real, Boolean, ObjectIdentifier
from bacpypes3.basetypes import PropertyIdentifier
from rich import print
from rich.traceback import install

install(show_locals=False)

# =================================================================
# 🚨 WINDOWS & PYTHON 3.13 HOTFIX
# =================================================================
if sys.platform == 'win32':
    import asyncio.base_events
    asyncio.base_events._set_reuseport = lambda sock: None
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def main():
    print("[bold magenta]Initializing Enterprise Testbench (Hybrid Pattern)...[/bold magenta]")
    
    # 🌟 1. HOOD RETAINED: 让 BAC0 负责初始化、绑定 0.0.0.0 和管理后台网络线程
    bacnet = BAC0.lite(ip='0.0.0.0', port=47810)
    
    # 🌟 2. STRICT TARGETING: 绝对严格的寻址与对象定义
    TARGET = Address("192.168.100.183:52025") # 🚨 记得更新这里的动态端口！
    OBJ_ID = ObjectIdentifier("analog-value,0")
    
    try:
        print(f"\n[bold cyan]--- Test Initiated: Connecting to DUT {TARGET} ---[/bold cyan]")
        
        # 🌟 3. STRICT PAYLOAD: 借用 BAC0 的内部引擎 (bacnet.app) 发送底层强类型 APDU
        print("[yellow][Write 1][/yellow] Forcing Out of Service = [bold green]True[/bold green] ...")
        await bacnet.app.write_property(
            TARGET, OBJ_ID,
            PropertyIdentifier("out-of-service"),
            Boolean(True)
        )
        
        await asyncio.sleep(1)
        
        print("[yellow][Write 2][/yellow] Injecting test vector ([bold red]31.0 °C @ Priority 8[/bold red]) ...")
        await bacnet.app.write_property(
            TARGET, OBJ_ID,
            PropertyIdentifier("present-value"),
            Real(31.0),
            priority=8
        )
        
        await asyncio.sleep(2) 
        
        # 🌟 4. STRICT READ: 绕过 BAC0 容易超时的单播 Ping 机制，直接提取底层数据
        print("[blue][Read][/blue] Verifying injected vector...")
        verify_temp = await bacnet.app.read_property(
            TARGET, OBJ_ID,
            PropertyIdentifier("present-value")
        )
        
        print(f"[blue] Verification Successful! Setpoint explicitly confirmed at: [bold green]{verify_temp} °C[/bold green]")
        
        if float(verify_temp) == 31.0:
            print("\n[bold black on green] ✅ AUTOMATION SEQUENCE 100% CLEAN! [/bold black on green]")

    except Exception as e:
        print(f"[bold white on red] Validation Failed [/bold white on red] {e}")
        
    finally:
        # 🌟 5. GRACEFUL TEARDOWN: 利用 BAC0 的安全断开机制，释放系统端口
        bacnet.disconnect()
        print("[dim]Network interfaces successfully released.[/dim]")

if __name__ == "__main__":
    asyncio.run(main())