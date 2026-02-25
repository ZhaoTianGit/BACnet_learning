import BAC0
import time

print("正在启动自动化测试平台...")

# 1. 启动 BACnet 网络。
# 注意：因为 Yabe 已经占用了默认的 47808 端口，我们让 Python 脚本用 47809 端口
# 这样 Yabe 和 Python 就可以同时运行，互不干扰！
bacnet = BAC0.lite(port=47809)

# 目标设备的 IP 地址 (从你的截图获取)
target_ip = '192.168.100.183'

try:
    print(f"\n--- 测试开始：连接设备 {target_ip} ---")
    
    # 2. 读取当前室温 (读取 Analog Input 0 的 Present Value)
    # 语法格式：bacnet.read('IP地址 对象类型 实例号 属性')
    current_temp = bacnet.read(f'{target_ip} analogInput 0 presentValue')
    print(f"[Read] 成功！当前房间的真实温度是: {current_temp} °C")
    
    time.sleep(2) # 停顿2秒，让你有时间看屏幕
    
    # 3. 写入新的设定温度 (修改 Analog Value 0 的 Present Value 为 24.5度)
    print(f"[Write] 正在下发控制指令，将设定温度修改为 24.5 °C...")
    bacnet.write(f'{target_ip} analogValue 0 presentValue 24.5')
    
    print("\n--- 测试通过！请观察你的 Room Simulator 界面！ ---")

except Exception as e:
    print(f"通讯失败，请检查网络或IP地址: {e}")

finally:
    # 结束测试，释放网络端口
    bacnet.disconnect()