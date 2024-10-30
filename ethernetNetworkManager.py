import asyncio
import subprocess
from networkController import ethernet_manager,redis_client
from debug_logger import DebugLogger

# Bu kod Abdulhamit Mercan tarafından Ekim 2024'te yazılmıştır.
# Bu koda https://github.com/abdulhamitmercan/networkProtokol adresinden erişebilirsiniz
# Bu kod, Ethernet kablosu bağlı olduğunda internet bağlantısını sorgular, 
# aksi durumlarda ise Ethernet bağlantısını kontrol etmeyip sonlandırır.
# Ethernet etkinliği, kablo durumu ve internet bağlantı durumu gibi çeşitli 
# bilgileri sorgulamak ve bu durumu sürekli güncellemek için kullanılır.




ethernet_enabled = ethernet_manager.isEnabled()  



class Ethernet:
    def __init__(self,logger=None):
        self._is_eth_up = False  
        self.cable_status = None  
        self.logger = logger
    @property
    def is_eth_up(self):
        return self._is_eth_up

    async def get_ethernet_info(self):
        # print("Ethernet Bilgileri:")
        result = subprocess.run(['ethtool', 'eth0'], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if "Speed:" in line or "Duplex:" in line or "Auto-negotiation:" in line or "Link detected:" in line:
                self.logger.info("", filename="ethernetNetworkManager.py", category="ethernet info", status=f"ethernet->info:{ line.strip()}")
                # print(line.strip())
        # print("") 

    async def check_cable_status(self):
      
        try:
            result = subprocess.run(['cat', '/sys/class/net/eth0/carrier'], capture_output=True, text=True)
            output = result.stdout.strip()
            if output == '':
                raise ValueError("Boş çıktı alındı.")  
            self.cable_status = int(output)
            temp = self.cable_status 
        except (ValueError, subprocess.CalledProcessError):
            self.logger.error("", filename="ethernetNetworkManager.py", category="ethernet info", status="eternet  down durumda  ve geçersiz çıktı alındı.")
            # print("eternet  down durumda  ve geçersiz çıktı alındı.")
            self.cable_status = 0  # Kablo yok gibi varsay
            temp = 69 # bayburtun plakası diye alınmıştır manası yoktur
            
        if temp == 0:
            self.logger.info("", filename="ethernetNetworkManager.py", category="ethernet info", status="Kablo takılı değil.")
            # print("Kablo takılı değil .")
        if temp == 1:
            self.logger.info("", filename="ethernetNetworkManager.py", category="ethernet info", status="Kablo takılı.")
            # print("Kablo bağlı.")

    async def toggle_ethernet(self):
        
        if ethernet_enabled:
            if not self.is_eth_up:  # Ethernet kapalıysa aç
                self.logger.info("", filename="ethernetNetworkManager.py", category="ethernet info", status="Ethernet etkinleştiriliyor...")
                # print("Ethernet etkinleştiriliyor...")
                subprocess.run(['sudo', 'ifconfig', 'eth0', 'up'])
                self._is_eth_up = True  
                self.logger.info("", filename="ethernetNetworkManager.py", category="ethernet info", status="Ethernet etkin.")
                # print("Ethernet etkin.")
        else:
            if self.is_eth_up:  # Ethernet açıksa kapat
                self.logger.info("", filename="ethernetNetworkManager.py", category="ethernet info", status="Ethernet devre dışı bırakılıyor...")
                # print("Ethernet devre dışı bırakılıyor...")
                subprocess.run(['sudo', 'ifconfig', 'eth0', 'down'])
                self._is_eth_up = False  
                self.logger.info("", filename="ethernetNetworkManager.py", category="ethernet info", status="Ethernet devre dışı")
                # print("Ethernet devre dışı.")

    async def check_ethernet_status(self):
       
        result = subprocess.run(['ip', 'link', 'show', 'eth0'], capture_output=True, text=True)
        if result.returncode == 0:
            if 'state UP' in result.stdout:
                self.logger.info("", filename="ethernetNetworkManager.py", category="ethernet info", status="Ethernet  aktive")
                # print("Ethernet  aktive")
                self._is_eth_up = True  
                await self.check_cable_status()  
                return True  
            elif 'state DOWN' in result.stdout:
                self.logger.info("", filename="ethernetNetworkManager.py", category="ethernet info", status="Ethernet   passive")
                # print("Ethernet    passive")
                self._is_eth_up = False  
                await self.check_cable_status()  
                return False  
        return None  

    async def check_internet_connection(self):
       
        if self.is_eth_up:  
            # self.logger.info("", filename="ethernetNetworkManager.py", category="ethernet info", status="ethernetin İnternet bağlantısı kontrol ediliyor...")
            print("ethernetin İnternet bağlantısı kontrol ediliyor...")
            result = subprocess.run(['ping', '-c', '1', '-I', 'eth0', '8.8.8.8'], capture_output=True, text=True)
            if result.returncode == 0:
                self.logger.info("", filename="ethernetNetworkManager.py", category="ethernet info", status="ethernetin İnternet bağlantısı mevcut.")
                # print("ethernetin İnternet bağlantısı mevcut.")
                await redis_client.hset("netWork", "ethernetInternetStatus", "1") # Ethernet İnternet bağlantısı var.
                await self.get_ethernet_info()  
                return True
            else:
                self.logger.info("", filename="ethernetNetworkManager.py", category="ethernet info", status="ethernetin İnternet bağlantısı yok.")
                # print("ethernetin İnternet bağlantısı yok.")
                await redis_client.hset("netWork", "ethernetInternetStatus", "0") # Ethernet İnternet bağlantısı yok.
                return False
        else:
            self.logger.info("", filename="ethernetNetworkManager.py", category="ethernet info", status="Ethernet durumu: DOWN, internet bağlantısı kontrol edilemez.")
            # print("Ethernet durumu: DOWN, internet bağlantısı kontrol edilemez.")
            await redis_client.hset("netWork", "ethernetInternetStatus", "0") #Ethernet İnternet bağlantısı yok.
            return False

    async def manage_ethernet(self):
       # bu kod eternetin kablosu bağlıysa internet durumunu sorgular aksi durumlarda kontrol sağlamaz 
        while True:
            await self.check_cable_status()  
            if self.cable_status == 1:  
                await self.check_ethernet_status() 
                await self.toggle_ethernet()         
                await self.check_internet_connection()
            else:
                await self.toggle_ethernet()
                await redis_client.hset("netWork", "ethernetInternetStatus", "0") #Ethernet İnternet bağlantısı yok.
            await asyncio.sleep(5)  

