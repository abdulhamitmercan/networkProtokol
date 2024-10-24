import redis.asyncio as redis
import asyncio
from  gsmNetworkManager import GsmModule
from ethernetNetworkManager import Ethernet
from wifiNetworkManager import WiFi
# Global nesneler
wifi_manager = None
ethernet_manager = None
gsm_manager = None
redis_client = None
class WifiManager:
    def __init__(self):
        self._enabled = True 

    def setEnabled(self, value):
        self._enabled = value

    def isEnabled(self):
        return self._enabled

    async def enable(self):
        print("Wi-Fi etkinleştirildi.")
        self.setEnabled(True)
     

    async def disable(self):
        print("Wi-Fi devre dışı bırakıldı.")
        self.setEnabled(False)
     


class EthernetManager:
    def __init__(self):
        self._enabled = True

    def setEnabled(self, value):
        self._enabled = value

    def isEnabled(self):
        return self._enabled

    async def enable(self):
        print("Ethernet etkinleştirildi.")
        self.setEnabled(True)
       

    async def disable(self):
        print("Ethernet devre dışı bırakıldı.")
        self.setEnabled(False)
       


class GsmManager:
    def __init__(self):
        self._enabled = True

    def setEnabled(self, value):
        self._enabled = value

    def isEnabled(self):
        return self._enabled

    async def enable(self):
        print("GSM etkinleştirildi.")
        self.setEnabled(True)
        

    async def disable(self):
        print("GSM devre dışı bırakıldı.")
        self.setEnabled(False)
        
wifi_manager = WifiManager()
ethernet_manager = EthernetManager()
gsm_manager = GsmManager()
redis_client = redis.Redis(host='localhost', port=6379, db=0)

class NetworkManager:
    def __init__(self):
        self._case_number = 8  
        
    def set_case_number(self, case_number):
        self._case_number = case_number

    def get_case_number(self):
        return self._case_number
    
    
    
    async def handle_case(self, case_number):
        if case_number == '1':
            await wifi_manager.enable()
            await ethernet_manager.disable()
            await gsm_manager.disable()
        elif case_number == '2':
            await ethernet_manager.enable()
            await wifi_manager.disable()
            await gsm_manager.disable()
        elif case_number == '3':
            await gsm_manager.enable()
            await wifi_manager.disable()
            await ethernet_manager.disable()
        elif case_number == '4':
            await wifi_manager.enable()
            await ethernet_manager.enable()
            await gsm_manager.disable()
        elif case_number == '5':
            await wifi_manager.enable()
            await gsm_manager.enable()
            await ethernet_manager.disable()
        elif case_number == '6':
            await ethernet_manager.enable()
            await gsm_manager.enable()
            await wifi_manager.disable()
        elif case_number == '7':
            await wifi_manager.enable()
            await ethernet_manager.enable()
            await gsm_manager.enable()
        elif case_number == '8':
            await wifi_manager.disable()
            await ethernet_manager.disable()
            await gsm_manager.disable()
        else:
            print("Geçersiz case numarası.")

    async def check_and_update(self):
        while True:
            self.set_case_number((int)(await redis_client.hget("netWork", "caseVal")))
            
            await asyncio.sleep(0.1)






async def main():
    network_manager = NetworkManager()
    gsm_module = GsmModule()
    ethernet_control = Ethernet()
    network_manager = WiFi()
    await asyncio.gather(network_manager.check_and_update(),
                         gsm_module.run_all_checks(),
                         ethernet_control.manage_ethernet(),
                         network_manager.manage_wifi()
                        )

asyncio.run(main())


